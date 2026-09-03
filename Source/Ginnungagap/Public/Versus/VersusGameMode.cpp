#include "Versus/VersusGameMode.h"

#include "AI/HorrorEnemy.h"
#include "GameFramework/GameSession.h"
#include "GameFramework/PlayerStart.h"
#include "Kismet/GameplayStatics.h"
#include "Threats/ShipThreatDirector.h"
#include "Versus/AntagonistPlayerCharacter.h"
#include "Versus/TeamAffiliationComponent.h"
#include "Versus/VersusGameState.h"
#include "Versus/VersusPlayerState.h"

AVersusGameMode::AVersusGameMode()
{
	GameStateClass = AVersusGameState::StaticClass();
	PlayerStateClass = AVersusPlayerState::StaticClass();
	AntagonistPawnClass = AAntagonistPlayerCharacter::StaticClass();
	bUseSeamlessTravel = true;
}

void AVersusGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
	Super::InitGame(MapName, Options, ErrorMessage);

	const int32 RequestedProtagonists = FCString::Atoi(*UGameplayStatics::ParseOption(Options, TEXT("Protagonists")));
	const int32 RequestedAntagonists = FCString::Atoi(*UGameplayStatics::ParseOption(Options, TEXT("Antagonists")));
	if (RequestedProtagonists > 0)
	{
		VersusSettings.ProtagonistSlots = RequestedProtagonists;
	}
	if (RequestedAntagonists > 0)
	{
		VersusSettings.AntagonistSlots = RequestedAntagonists;
	}

	const EAntagonistFaction RequestedFaction = ParseFaction(
		UGameplayStatics::ParseOption(Options, TEXT("AntagonistFaction")));
	if (RequestedFaction != EAntagonistFaction::None)
	{
		VersusSettings.PlayerAntagonistFaction = RequestedFaction;
	}

	TArray<FString> AIFactionNames;
	UGameplayStatics::ParseOption(Options, TEXT("IndependentAI")).ParseIntoArray(
		AIFactionNames, TEXT(","), true);
	for (const FString& Name : AIFactionNames)
	{
		const EAntagonistFaction Faction = ParseFaction(Name);
		if (Faction != EAntagonistFaction::None)
		{
			VersusSettings.IndependentAIFactions.AddUnique(Faction);
		}
	}
	VersusSettings.Sanitize();

	if (GameSession)
	{
		GameSession->MaxPlayers = VersusSettings.GetMaxPlayers();
	}
}

void AVersusGameMode::BeginPlay()
{
	Super::BeginPlay();
	if (AVersusGameState* State = GetGameState<AVersusGameState>())
	{
		State->SetMatchSettings(VersusSettings);
	}
	SpawnIndependentFactions();
}

void AVersusGameMode::PreLogin(const FString& Options, const FString& Address,
	const FUniqueNetIdRepl& UniqueId, FString& ErrorMessage)
{
	Super::PreLogin(Options, Address, UniqueId, ErrorMessage);
	if (!ErrorMessage.IsEmpty())
	{
		return;
	}
	const AVersusGameState* State = GetGameState<AVersusGameState>();
	if (State && State->PlayerArray.Num() >= VersusSettings.GetMaxPlayers())
	{
		ErrorMessage = TEXT("VERSUS_MATCH_FULL");
	}
}

FString AVersusGameMode::InitNewPlayer(APlayerController* NewPlayerController,
	const FUniqueNetIdRepl& UniqueId, const FString& Options, const FString& Portal)
{
	const FString Result = Super::InitNewPlayer(NewPlayerController, UniqueId, Options, Portal);
	if (AVersusPlayerState* State = NewPlayerController
		? NewPlayerController->GetPlayerState<AVersusPlayerState>() : nullptr)
	{
		const EVersusTeam Team = ChooseTeam(Options);
		State->SetVersusIdentity(Team, Team == EVersusTeam::Antagonist
			? VersusSettings.PlayerAntagonistFaction : EAntagonistFaction::None);
		if (Team == EVersusTeam::Antagonist)
		{
			State->GrantAntagonistSkillPoints(StartingAntagonistSkillPoints);
		}
	}
	return Result;
}

void AVersusGameMode::PostLogin(APlayerController* NewPlayer)
{
	Super::PostLogin(NewPlayer);
	if (AVersusPlayerState* PlayerState = NewPlayer
		? NewPlayer->GetPlayerState<AVersusPlayerState>() : nullptr;
		PlayerState && PlayerState->VersusTeam == EVersusTeam::Antagonist)
	{
		if (AVersusGameState* State = GetGameState<AVersusGameState>(); State && !State->HasCommander())
		{
			State->TryClaimCommander(PlayerState);
		}
	}
	RefreshMatchPhase();
}

void AVersusGameMode::Logout(AController* Exiting)
{
	if (AVersusGameState* State = GetGameState<AVersusGameState>())
	{
		State->ReleaseCommander(Exiting ? Exiting->GetPlayerState<AVersusPlayerState>() : nullptr);
	}
	Super::Logout(Exiting);
	RefreshMatchPhase();
}

UClass* AVersusGameMode::GetDefaultPawnClassForController_Implementation(AController* InController)
{
	const AVersusPlayerState* State = InController
		? InController->GetPlayerState<AVersusPlayerState>() : nullptr;
	if (State && State->VersusTeam == EVersusTeam::Antagonist && AntagonistPawnClass)
	{
		return AntagonistPawnClass;
	}
	return Super::GetDefaultPawnClassForController_Implementation(InController);
}

void AVersusGameMode::RestartPlayer(AController* NewPlayer)
{
	Super::RestartPlayer(NewPlayer);
	ApplyPlayerAffiliation(NewPlayer);
}

EVersusTeam AVersusGameMode::ChooseTeam(const FString& Options) const
{
	const AVersusGameState* State = GetGameState<AVersusGameState>();
	const int32 Protagonists = State ? State->GetTeamPlayerCount(EVersusTeam::Protagonist) : 0;
	const int32 Antagonists = State ? State->GetTeamPlayerCount(EVersusTeam::Antagonist) : 0;
	const FString RequestedTeam = UGameplayStatics::ParseOption(Options, TEXT("Team"));

	if (RequestedTeam.Equals(TEXT("Antagonist"), ESearchCase::IgnoreCase)
		&& Antagonists < VersusSettings.AntagonistSlots)
	{
		return EVersusTeam::Antagonist;
	}
	if (RequestedTeam.Equals(TEXT("Protagonist"), ESearchCase::IgnoreCase)
		&& Protagonists < VersusSettings.ProtagonistSlots)
	{
		return EVersusTeam::Protagonist;
	}

	if (Protagonists >= VersusSettings.ProtagonistSlots)
	{
		return Antagonists < VersusSettings.AntagonistSlots
			? EVersusTeam::Antagonist : EVersusTeam::Spectator;
	}
	if (Antagonists >= VersusSettings.AntagonistSlots)
	{
		return EVersusTeam::Protagonist;
	}

	// Fill toward the configured team ratio. The listen host becomes protagonist; the next
	// unassigned player fills antagonist in the common 1v1 and 4v1 configurations.
	return Antagonists * VersusSettings.ProtagonistSlots
		< Protagonists * VersusSettings.AntagonistSlots
		? EVersusTeam::Antagonist : EVersusTeam::Protagonist;
}

void AVersusGameMode::ApplyPlayerAffiliation(AController* Controller) const
{
	if (!Controller || !Controller->GetPawn())
	{
		return;
	}
	const AVersusPlayerState* State = Controller->GetPlayerState<AVersusPlayerState>();
	UTeamAffiliationComponent* Affiliation =
		Controller->GetPawn()->FindComponentByClass<UTeamAffiliationComponent>();
	if (!State || !Affiliation)
	{
		return;
	}
	Affiliation->SetAffiliation(State->VersusTeam, State->AntagonistFaction);
	if (AAntagonistPlayerCharacter* Antagonist = Cast<AAntagonistPlayerCharacter>(Controller->GetPawn()))
	{
		Antagonist->ConfigureForFaction(State->AntagonistFaction);
	}
}

void AVersusGameMode::RefreshMatchPhase() const
{
	if (AVersusGameState* State = GetGameState<AVersusGameState>())
	{
		State->SetMatchPhase(State->HasMinimumPlayers()
			? EVersusMatchPhase::Warmup : EVersusMatchPhase::WaitingForPlayers);
	}
}

void AVersusGameMode::SpawnIndependentFactions()
{
	if (!HasAuthority() || !GetWorld())
	{
		return;
	}

	int32 SpawnOffset = 0;
	for (const EAntagonistFaction Faction : VersusSettings.IndependentAIFactions)
	{
		if (Faction == EAntagonistFaction::Bloom)
		{
			for (int32 Index = 0; Index < 3; ++Index)
			{
				const FVector Location = FVector(350.0f * Index, 450.0f + SpawnOffset, 100.0f);
				GetWorld()->SpawnActor<AHorrorEnemy>(AHorrorEnemy::StaticClass(), Location, FRotator::ZeroRotator);
			}
			SpawnOffset += 500;
			continue;
		}

		EThreatEncounterPreset Preset = EThreatEncounterPreset::AlienHuntingPack;
		if (Faction == EAntagonistFaction::Pirates)
		{
			Preset = EThreatEncounterPreset::PirateBoarding;
		}
		else if (Faction == EAntagonistFaction::Rebels)
		{
			Preset = EThreatEncounterPreset::RebelTakeover;
		}

		const FTransform Transform(FRotator::ZeroRotator, FVector(0.0f, 500.0f + SpawnOffset, 100.0f));
		AShipThreatDirector* Director = GetWorld()->SpawnActorDeferred<AShipThreatDirector>(
			AShipThreatDirector::StaticClass(), Transform, nullptr, nullptr,
			ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
		if (Director)
		{
			Director->Preset = Preset;
			Director->bAutoStart = true;
			Director->FinishSpawning(Transform);
		}
		SpawnOffset += 500;
	}
}

EAntagonistFaction AVersusGameMode::ParseFaction(const FString& Value)
{
	if (Value.Equals(TEXT("Bloom"), ESearchCase::IgnoreCase)) return EAntagonistFaction::Bloom;
	if (Value.Equals(TEXT("Pirates"), ESearchCase::IgnoreCase)) return EAntagonistFaction::Pirates;
	if (Value.Equals(TEXT("Rebels"), ESearchCase::IgnoreCase)) return EAntagonistFaction::Rebels;
	if (Value.Equals(TEXT("Alien"), ESearchCase::IgnoreCase)) return EAntagonistFaction::Alien;
	return EAntagonistFaction::None;
}
