#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Camera/CameraActor.h"
#include "Rendering/SkeletalMeshLODRenderData.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Engine/StaticMeshActor.h"
#include "Animation/SkeletalMeshActor.h"
#include "UObject/UObjectIterator.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Texture.h"
#include "Materials/MaterialInstance.h"
#include "EngineUtils.h"
#include "UnrealClient.h"

#include "CoopSurvivalCharacter.h"
#include "Kismet/GameplayStatics.h"
#include "Player/SurvivalPlayerController.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "LevelSetup/QuickDemoOpeningSequence.h"
#include "Weapons/ShipboardWeapon.h"
#include "Weapons/WeaponMountComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Camera/CameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimInstance.h"
#include "Engine/SkeletalMesh.h"
#include "Components/PrimitiveComponent.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

#include "Tests/GinnungagapTestMap.h"

/**
 * Stills of the opening, one per phase, captured on phase change from the player's own view.
 * A look test: it asserts only that the sequence runs through to first person. Its value is the
 * pictures -- Opening_<phase>.png under Saved/Screenshots -- which a windowed run produces in
 * under two minutes, against twenty-five for a full recording of the walk. Under -nullrhi the
 * pictures are black and only the phase assertions mean anything.
 */
namespace OpeningLook
{
	UWorld* FindPieWorld()
	{
		if (!GEngine)
		{
			return nullptr;
		}
		for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			if (Context.WorldType == EWorldType::PIE && Context.World())
			{
				return Context.World();
			}
		}
		return nullptr;
	}

	const TCHAR* PhaseName(EQuickDemoOpeningPhase Phase)
	{
		switch (Phase)
		{
		case EQuickDemoOpeningPhase::Asleep:      return TEXT("1_asleep");
		case EQuickDemoOpeningPhase::Strike:      return TEXT("2_strike");
		case EQuickDemoOpeningPhase::Blackout:    return TEXT("3_blackout");
		case EQuickDemoOpeningPhase::Wake:        return TEXT("4_wake");
		case EQuickDemoOpeningPhase::ClimbOut:    return TEXT("5_climb_out");
		case EQuickDemoOpeningPhase::FirstPerson: return TEXT("6_first_person");
		default:                                  return nullptr;
		}
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FCaptureOpeningPhases, FAutomationTestBase*, Test);

bool FCaptureOpeningPhases::Update()
{
	static EQuickDemoOpeningPhase LastCaptured = EQuickDemoOpeningPhase::Idle;
	static double PhaseEnteredAt = -1.0;
	UWorld* World = OpeningLook::FindPieWorld();
	if (!World)
	{
		return false;
	}
	AQuickDemoOpeningSequence* Opening = nullptr;
	for (TActorIterator<AQuickDemoOpeningSequence> It(World); It; ++It)
	{
		Opening = *It;
		break;
	}
	if (!Test->TestNotNull(TEXT("The demo map has an opening sequence"), Opening))
	{
		LastCaptured = EQuickDemoOpeningPhase::Idle;
		return true;
	}
	const double Now = World->GetTimeSeconds();
	const EQuickDemoOpeningPhase Phase = Opening->GetPhase();
	if (Phase != LastCaptured)
	{
		if (PhaseEnteredAt < 0.0)
		{
			PhaseEnteredAt = Now;
			UE_LOG(LogTemp, Display, TEXT("OPENINGLOOK phase %d at t=%.2f"), static_cast<int32>(Phase), Now);
		}
		// Half a second into the phase, so the picture is of the phase and not of the cut into it.
		// (First person completes almost at once, so it is caught sooner.)
		if (Now - PhaseEnteredAt >= (Phase == EQuickDemoOpeningPhase::FirstPerson ? 0.15 : 0.5))
		{
			if (const TCHAR* Name = OpeningLook::PhaseName(Phase))
			{
				FScreenshotRequest::RequestScreenshot(FString::Printf(TEXT("Opening_%s"), Name), false, false, false, FIntRect(), true);
			}
			LastCaptured = Phase;
			PhaseEnteredAt = -1.0;
		}
	}
	// Awake in the tube, the crew presses the release: the pod does not open itself. A moment
	// after the wake still has been taken, so the tube is seen awake and shut first.
	if (Phase == EQuickDemoOpeningPhase::Wake && LastCaptured == EQuickDemoOpeningPhase::Wake)
	{
		if (ASurvivalPlayerController* PC = Cast<ASurvivalPlayerController>(UGameplayStatics::GetPlayerController(World, 0))) { PC->PressInteract(); }
	}
	if (Opening->IsComplete() || Now > 30.0)
	{
		Test->TestTrue(TEXT("The opening ran through to completion within 30s"), Opening->IsComplete());
		LastCaptured = EQuickDemoOpeningPhase::Idle;
		PhaseEnteredAt = -1.0;
		return true;
	}
	return false;
}

/** The workshop grant, applied directly, and a still of the tool in hand a moment later. */
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FCaptureToolInHand, FAutomationTestBase*, Test);

bool FCaptureToolInHand::Update()
{
	static double GrantedAt = 0.0;
	UWorld* World = OpeningLook::FindPieWorld();
	if (!World)
	{
		return true;
	}
	if (GrantedAt == 0.0)
	{
		AQuickDemoWorkshopBench* Bench = nullptr;
		for (TActorIterator<AQuickDemoWorkshopBench> It(World); It; ++It)
		{
			Bench = *It;
			break;
		}
		ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(UGameplayStatics::GetPlayerPawn(World, 0));
		if (!Test->TestNotNull(TEXT("The demo map has a workshop bench"), Bench) || !Test->TestNotNull(TEXT("There is a player character"), Character))
		{
			return true;
		}
		Bench->OnActivityCompleted_Implementation(Character);
		GrantedAt = World->GetTimeSeconds();
		return false;
	}
	if (World->GetTimeSeconds() - GrantedAt < 0.7)
	{
		return false;
	}
	FScreenshotRequest::RequestScreenshot(TEXT("Opening_7_tool_in_hand"), true, false, false, FIntRect(), true);
	// Where the tool actually sits relative to the view, so a backwards mesh can be told from a
	// backwards mount from the log alone.
	if (ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)))
	{
		if (UWeaponMountComponent* Mount = Character->FindComponentByClass<UWeaponMountComponent>())
		{
			const FVector View = Character->GetBaseAimRotation().Vector();
			FString HandInfo;
			if (Character->GetFirstPersonCamera() && Character->GetMesh())
			{
				const FTransform Cam = Character->GetFirstPersonCamera()->GetComponentTransform();
				const FVector HandInCam = Cam.InverseTransformPosition(Character->GetMesh()->GetSocketLocation(TEXT("hand_r")));
				const FVector MountInCam = Cam.InverseTransformPosition(Mount->GetComponentLocation());
				HandInfo = FString::Printf(TEXT(" hand_r in camera space %s, mount in camera space %s,"), *HandInCam.ToCompactString(), *MountInCam.ToCompactString());
			}
			const FString MountInfo = FString::Printf(TEXT("mount rel loc %s rel rot %s,%s forward.view %.2f"),
				*Mount->GetRelativeLocation().ToCompactString(), *Mount->GetRelativeRotation().ToCompactString(), *HandInfo,
				FVector::DotProduct(Mount->GetForwardVector(), View));
			if (AShipboardWeapon* Weapon = Mount->GetMountedWeapon())
			{
				UE_LOG(LogTemp, Display, TEXT("TOOLLOOK %s: weapon %s forward.view %.2f, mesh rel rot %s"), *MountInfo, *Weapon->GetClass()->GetName(),
					FVector::DotProduct(Weapon->GetActorForwardVector(), View),
					Weapon->VisualMesh ? *Weapon->VisualMesh->GetRelativeRotation().ToCompactString() : TEXT("-"));
			}
			else
			{
				UE_LOG(LogTemp, Display, TEXT("TOOLLOOK %s: nothing mounted"), *MountInfo);
			}
		}
	}
	GrantedAt = 0.0;
	return true;
}

/**
 * The crew in third person after the opening, from a camera two metres in front: is the suit the
 * Space Marshal (the Fab primary oversuit) and not a development shell? One still, then back to
 * first person.
 */
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FCaptureSuitedThirdPerson, FAutomationTestBase*, Test);

bool FCaptureSuitedThirdPerson::Update()
{
	// 0: place the camera; 1: settle, then request the shot; 2: let it render, then restore.
	static int32 Phase = 0;
	static double PhaseAt = -1.0;
	static TWeakObjectPtr<ACameraActor> Camera;
	UWorld* World = OpeningLook::FindPieWorld();
	ACoopSurvivalCharacter* Character = World ? Cast<ACoopSurvivalCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)) : nullptr;
	APlayerController* PC = World ? UGameplayStatics::GetPlayerController(World, 0) : nullptr;
	if (!Character || !PC)
	{
		Phase = 0; PhaseAt = -1.0;
		return true;
	}
	const double Now = World->GetTimeSeconds();
	if (Phase == 0)
	{
		// The crew wake in the bodysuit and draw the suit at the rack; this still is about the suit,
		// so put it on them here.
		if (!Character->bPressureOversuitEquipped) { Character->SetPressureOversuitEquipped(true); }
		// Front-left of the crew, since straight ahead is the pod they just left; spawned regardless
		// of what the spot overlaps, a camera has no collision to speak of.
		// Close, at chest height: the straps and the shoulder patch are the proof of a textured suit.
		const FVector Eye = Character->GetActorLocation() + Character->GetActorForwardVector() * 170.0f
			- Character->GetActorRightVector() * 30.0f + FVector(0, 0, 35.0f);
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		ACameraActor* Cam = World->SpawnActor<ACameraActor>(Eye, (Character->GetActorLocation() + Character->GetActorRightVector() * 50.0f + FVector(0, 0, 20.0f) - Eye).Rotation(), Params);
		Test->TestNotNull(TEXT("A camera for the suited still spawned"), Cam);
		Camera = Cam;
		// The view switch re-targets the controller to the character; the camera must come after.
		Character->SetFirstPersonView(false);
		if (Camera.IsValid()) { PC->SetViewTargetWithBlend(Camera.Get(), 0.0f); }
		// The suit's 4K set has only its base mips resident this early; ask for the rest now.
		if (USkeletalMeshComponent* Oversuit = Character->GetPrimaryOversuitMesh()) { Oversuit->PrestreamTextures(6.0f, true); }
		Phase = 1; PhaseAt = Now;
		return false;
	}
	if (Phase == 1)
	{
		if (Camera.IsValid() && PC->GetViewTarget() != Camera.Get()) { PC->SetViewTargetWithBlend(Camera.Get(), 0.0f); }
		if (Now - PhaseAt < 3.0) { return false; }
		if (USkeletalMeshComponent* Oversuit = Character->GetPrimaryOversuitMesh())
		{
			TArray<UTexture*> Textures;
			Oversuit->GetUsedTextures(Textures, EMaterialQualityLevel::High);
			int32 Streamed = 0;
			for (UTexture* T : Textures) { if (T && T->IsFullyStreamedIn()) { ++Streamed; } }
			UE_LOG(LogTemp, Display, TEXT("SUITLOOK %d of %d suit textures fully streamed in"), Streamed, Textures.Num());
		}
		UE_LOG(LogTemp, Display, TEXT("SUITLOOK view target %s (camera %s at %s), pawn at %s, first person %d"),
			PC->GetViewTarget() ? *PC->GetViewTarget()->GetName() : TEXT("none"), Camera.IsValid() ? *Camera->GetName() : TEXT("invalid"),
			Camera.IsValid() ? *Camera->GetActorLocation().ToCompactString() : TEXT("-"), *Character->GetActorLocation().ToCompactString(),
			Character->IsFirstPersonView() ? 1 : 0);
		// The shot renders a frame after the request; the view goes back to the crew only after.
		FScreenshotRequest::RequestScreenshot(TEXT("Opening_8_suited_third_person"), false, false, false, FIntRect(), true);
		Phase = 2; PhaseAt = Now;
		return false;
	}
	if (Now - PhaseAt < 0.3) { return false; }
	if (USkeletalMeshComponent* Oversuit = Character->GetPrimaryOversuitMesh())
	{
		UE_LOG(LogTemp, Display, TEXT("SUITLOOK primary oversuit %s visible %d"), Oversuit->GetSkeletalMeshAsset() ? *Oversuit->GetSkeletalMeshAsset()->GetPathName() : TEXT("none"), Oversuit->IsVisible() ? 1 : 0);
		for (int32 Slot = 0; Slot < Oversuit->GetNumMaterials(); ++Slot)
		{
			UMaterialInterface* M = Oversuit->GetMaterial(Slot);
			const UMaterialInstance* Inst = Cast<UMaterialInstance>(M);
			UE_LOG(LogTemp, Display, TEXT("SUITLOOK slot %d: %s (parent %s)"), Slot, M ? *M->GetPathName() : TEXT("none"),
				Inst && Inst->Parent ? *Inst->Parent->GetPathName() : TEXT("-"));
		}
	}
	PC->SetViewTargetWithBlend(Character, 0.0f);
	Character->SetFirstPersonView(true);
	if (Camera.IsValid()) { Camera->Destroy(); }
	Phase = 0; PhaseAt = -1.0;
	return true;
}

/**
 * The suit rack in the cryo bay, from two and a half metres in front: the Space Marshal hanging
 * from its rail beside the locker, before anyone has taken it. One still, then the view returns.
 */
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FCaptureSuitRack, FAutomationTestBase*, Test);

bool FCaptureSuitRack::Update()
{
	static int32 Phase = 0;
	static double PhaseAt = -1.0;
	static TWeakObjectPtr<ACameraActor> Camera;
	UWorld* World = OpeningLook::FindPieWorld();
	ACoopSurvivalCharacter* Character = World ? Cast<ACoopSurvivalCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)) : nullptr;
	APlayerController* PC = World ? UGameplayStatics::GetPlayerController(World, 0) : nullptr;
	AQuickDemoSuitStation* Rack = nullptr;
	if (World) { for (TActorIterator<AQuickDemoSuitStation> It(World); It; ++It) { Rack = *It; break; } }
	if (!Character || !PC || !Rack)
	{
		Phase = 0; PhaseAt = -1.0;
		return true;
	}
	const double Now = World->GetTimeSeconds();
	if (Phase == 0)
	{
		const FVector Target = Rack->GetActorLocation() + Rack->GetActorForwardVector() * 55.0f;
		const FVector Eye = Target + Rack->GetActorForwardVector() * 250.0f - Rack->GetActorRightVector() * 90.0f + FVector(0, 0, 10.0f);
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		ACameraActor* Cam = World->SpawnActor<ACameraActor>(Eye, (Target - Eye).Rotation(), Params);
		Camera = Cam;
		if (Cam) { PC->SetViewTargetWithBlend(Cam, 0.0f); }
		if (Rack->RackSuit) { Rack->RackSuit->PrestreamTextures(6.0f, true); }
		UE_LOG(LogTemp, Display, TEXT("RACKLOOK rack %s at %s, suit visible %d taken %d"), *Rack->GetName(), *Rack->GetActorLocation().ToCompactString(),
			Rack->RackSuit && Rack->RackSuit->IsVisible() ? 1 : 0, Rack->bSuitTaken ? 1 : 0);
		Phase = 1; PhaseAt = Now;
		return false;
	}
	if (Phase == 1)
	{
		if (Now - PhaseAt < 2.5) { return false; }
		FScreenshotRequest::RequestScreenshot(TEXT("Opening_9_suit_rack"), false, false, false, FIntRect(), true);
		Phase = 2; PhaseAt = Now;
		return false;
	}
	if (Now - PhaseAt < 0.3) { return false; }
	PC->SetViewTargetWithBlend(Character, 0.0f);
	if (Camera.IsValid()) { Camera->Destroy(); }
	Phase = 0; PhaseAt = -1.0;
	return true;
}

/**
 * The hold pose from each candidate hold animation, one still each, with the hand's position in
 * camera space logged: the numbers pick the variant (forward, slightly right, a little below the
 * eye), the stills confirm it.
 */
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FSweepHoldPose, FAutomationTestBase*, Test);

bool FSweepHoldPose::Update()
{
	// The one the character uses; add names here (and build them with
	// tools/build_tool_hold_additive_anim.py --sweep) to compare candidates again.
	static const TCHAR* Variants[] = { TEXT("A_ToolHold_Combo_B") };
	static int32 Index = 0;
	static double SetAt = -1.0;
	UWorld* World = OpeningLook::FindPieWorld();
	ACoopSurvivalCharacter* Character = World ? Cast<ACoopSurvivalCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)) : nullptr;
	UWeaponMountComponent* Mount = Character ? Character->FindComponentByClass<UWeaponMountComponent>() : nullptr;
	if (!Mount || !Mount->GetMountedWeapon() || !Character->GetFirstPersonCamera() || !Character->GetMesh())
	{
		Index = 0; SetAt = -1.0;
		return true;
	}
	const double Now = World->GetTimeSeconds();
	if (SetAt < 0.0)
	{
		UAnimSequenceBase* Variant = LoadObject<UAnimSequenceBase>(nullptr,
			*FString::Printf(TEXT("/Game/Characters/Mannequins/Anims/Tools/%s.%s"), Variants[Index], Variants[Index]));
		if (!Variant)
		{
			UE_LOG(LogTemp, Display, TEXT("HOLDSWEEP %s missing"), Variants[Index]);
			if (++Index >= UE_ARRAY_COUNT(Variants)) { Index = 0; return true; }
			return false;
		}
		Character->HoldAnimation = Variant;
		Character->HoldAnimationTime = 1.6f;
		Character->HandleMountedWeaponChanged(Mount->GetMountedWeapon());
		SetAt = Now;
		return false;
	}
	if (Now - SetAt < 0.8)
	{
		return false;
	}
	const FTransform Cam = Character->GetFirstPersonCamera()->GetComponentTransform();
	UE_LOG(LogTemp, Display, TEXT("HOLDSWEEP %s hand_r in camera space %s"), Variants[Index],
		*Cam.InverseTransformPosition(Character->GetMesh()->GetSocketLocation(TEXT("hand_r"))).ToCompactString());
	FScreenshotRequest::RequestScreenshot(FString::Printf(TEXT("Hold_%02d_%s"), Index, Variants[Index]), true, false, false, FIntRect(), true);
	++Index; SetAt = -1.0;
	if (Index >= UE_ARRAY_COUNT(Variants))
	{
		Index = 0;
		return true;
	}
	return false;
}

namespace ToolboxShaders
{
	/**
	 * The hand tool's materials are not referenced by the map, so their shaders first compile when
	 * the workshop bench spawns it -- asynchronously, with the default material drawn meanwhile.
	 * A capture a few seconds later shows a flat, untextured tool. Load them ahead of PIE so the
	 * wait-for-shaders command below covers them.
	 */
	inline void Preload()
	{
		for (const TCHAR* Path : { TEXT("/Game/Frontier_EngineersToolbox/Materials/M_FrontierTools_1.M_FrontierTools_1"),
			TEXT("/Game/Frontier_EngineersToolbox/Materials/M_FrontierTools_Toolbox1.M_FrontierTools_Toolbox1"),
			TEXT("/Game/Frontier_EngineersToolbox/Tools/SM_Frontier_Powertool.SM_Frontier_Powertool") })
		{
			LoadObject<UObject>(nullptr, Path);
		}
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapOpeningShotLookTest,
	"Ginnungagap.Look.OpeningShots",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapOpeningShotLookTest::RunTest(const FString& Parameters)
{
	AutomationOpenMap(GinnungagapTestMap::Path());
	ToolboxShaders::Preload();
	// A checkpoint left by an earlier run (the keyboard test saves one) would resume the crew mid-
	// mission and skip the opening; this test is about the opening, so it starts clean.
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForShadersToFinishCompilingInGame());
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FCaptureOpeningPhases(this));
	ADD_LATENT_AUTOMATION_COMMAND(FCaptureToolInHand(this));
	ADD_LATENT_AUTOMATION_COMMAND(FSweepHoldPose(this));
	ADD_LATENT_AUTOMATION_COMMAND(FCaptureSuitedThirdPerson(this));
	ADD_LATENT_AUTOMATION_COMMAND(FCaptureSuitRack(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
