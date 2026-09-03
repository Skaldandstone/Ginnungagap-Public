#include "Meta/MultiplayerSessionSubsystem.h"
#include "OnlineSubsystem.h"
#include "OnlineSessionSettings.h"
#include "Online/OnlineSessionNames.h"
#include "GameFramework/PlayerController.h"
#include "Engine/GameInstance.h"
#include "Engine/Engine.h"

void UMultiplayerSessionSubsystem::Initialize(FSubsystemCollectionBase& Collection){Super::Initialize(Collection);if(IOnlineSubsystem* Online=IOnlineSubsystem::Get())SessionInterface=Online->GetSessionInterface();if(GEngine){NetworkFailureHandle=GEngine->OnNetworkFailure().AddUObject(this,&UMultiplayerSessionSubsystem::HandleNetworkFailure);TravelFailureHandle=GEngine->OnTravelFailure().AddUObject(this,&UMultiplayerSessionSubsystem::HandleTravelFailure);}}
void UMultiplayerSessionSubsystem::Deinitialize(){if(GEngine){GEngine->OnNetworkFailure().Remove(NetworkFailureHandle);GEngine->OnTravelFailure().Remove(TravelFailureHandle);}if(SessionInterface.IsValid()){if(CreateDelegateHandle.IsValid())SessionInterface->ClearOnCreateSessionCompleteDelegate_Handle(CreateDelegateHandle);if(DestroyDelegateHandle.IsValid())SessionInterface->ClearOnDestroySessionCompleteDelegate_Handle(DestroyDelegateHandle);if(FindDelegateHandle.IsValid())SessionInterface->ClearOnFindSessionsCompleteDelegate_Handle(FindDelegateHandle);if(JoinDelegateHandle.IsValid())SessionInterface->ClearOnJoinSessionCompleteDelegate_Handle(JoinDelegateHandle);}SessionSearch.Reset();SessionInterface.Reset();Super::Deinitialize();}

void UMultiplayerSessionSubsystem::HostSession(int32 PublicConnections,const FString& MapName,bool bIsLAN)
{
	PendingConnections=FMath::Clamp(PublicConnections,2,12);PendingMapName=MapName;bPendingLAN=bIsLAN;
	if(!SessionInterface.IsValid()){OnHostSessionComplete.Broadcast(false,TEXT("Online session provider is unavailable."));return;}
	if(SessionInterface->GetNamedSession(NAME_GameSession))
	{
		bRecreateAfterDestroy=true;bLeavingSession=false;
		DestroyDelegateHandle=SessionInterface->AddOnDestroySessionCompleteDelegate_Handle(FOnDestroySessionCompleteDelegate::CreateUObject(this,&UMultiplayerSessionSubsystem::HandleDestroySessionComplete));
		if(!SessionInterface->DestroySession(NAME_GameSession)){SessionInterface->ClearOnDestroySessionCompleteDelegate_Handle(DestroyDelegateHandle);DestroyDelegateHandle.Reset();OnHostSessionComplete.Broadcast(false,TEXT("Could not replace the existing crew session."));}
		return;
	}
	CreateSessionNow();
}

void UMultiplayerSessionSubsystem::LeaveCrewSession()
{
	if(!bSessionActive){OnLeaveCrewSessionComplete.Broadcast(true,FString());return;}
	if(!SessionInterface.IsValid()){OnLeaveCrewSessionComplete.Broadcast(false,TEXT("Online session provider is unavailable."));return;}
	bRecreateAfterDestroy=false;bLeavingSession=true;
	DestroyDelegateHandle=SessionInterface->AddOnDestroySessionCompleteDelegate_Handle(FOnDestroySessionCompleteDelegate::CreateUObject(this,&UMultiplayerSessionSubsystem::HandleDestroySessionComplete));
	if(!SessionInterface->DestroySession(NAME_GameSession))
	{
		SessionInterface->ClearOnDestroySessionCompleteDelegate_Handle(DestroyDelegateHandle);DestroyDelegateHandle.Reset();bLeavingSession=false;
		OnLeaveCrewSessionComplete.Broadcast(false,TEXT("The crew session could not be closed."));
	}
}

void UMultiplayerSessionSubsystem::CreateSessionNow()
{
	FOnlineSessionSettings Settings;Settings.bIsLANMatch=bPendingLAN;Settings.NumPublicConnections=PendingConnections;Settings.bShouldAdvertise=true;Settings.bAllowJoinInProgress=true;Settings.bAllowJoinViaPresence=true;Settings.bUsesPresence=true;Settings.bUseLobbiesIfAvailable=true;
	Settings.Set(SETTING_MAPNAME,PendingMapName,EOnlineDataAdvertisementType::ViaOnlineServiceAndPing);Settings.Set(FName(TEXT("GINNUNGAGAP_BUILD")),FString(TEXT("prototype-01")),EOnlineDataAdvertisementType::ViaOnlineServiceAndPing);
	CreateDelegateHandle=SessionInterface->AddOnCreateSessionCompleteDelegate_Handle(FOnCreateSessionCompleteDelegate::CreateUObject(this,&UMultiplayerSessionSubsystem::HandleCreateSessionComplete));
	if(!SessionInterface->CreateSession(0,NAME_GameSession,Settings)){SessionInterface->ClearOnCreateSessionCompleteDelegate_Handle(CreateDelegateHandle);CreateDelegateHandle.Reset();OnHostSessionComplete.Broadcast(false,TEXT("The crew session could not be started."));}
}

void UMultiplayerSessionSubsystem::HandleCreateSessionComplete(FName SessionName,bool bWasSuccessful)
{
	if(SessionInterface.IsValid())SessionInterface->ClearOnCreateSessionCompleteDelegate_Handle(CreateDelegateHandle);
	CreateDelegateHandle.Reset();
	if(bWasSuccessful)
	{
		UGameInstance* GI=GetGameInstance();
		bWasSuccessful=GI&&GI->EnableListenServer(true);
		if(!bWasSuccessful&&SessionInterface.IsValid())SessionInterface->DestroySession(NAME_GameSession);
	}
	bSessionActive=bWasSuccessful;bIsHost=bWasSuccessful;
	OnHostSessionComplete.Broadcast(bWasSuccessful,bWasSuccessful?FString():TEXT("The crew session was created, but the host could not open a listen server."));
}
void UMultiplayerSessionSubsystem::HandleDestroySessionComplete(FName SessionName,bool bWasSuccessful)
{
	if(SessionInterface.IsValid())SessionInterface->ClearOnDestroySessionCompleteDelegate_Handle(DestroyDelegateHandle);DestroyDelegateHandle.Reset();
	const bool bWasLeaving=bLeavingSession;bLeavingSession=false;
	if(bWasSuccessful)
	{
		const bool bWasHost=bIsHost;bSessionActive=false;bIsHost=false;
		if(bWasLeaving&&bWasHost)if(UGameInstance* GI=GetGameInstance())GI->EnableListenServer(false);
		if(bRecreateAfterDestroy){bRecreateAfterDestroy=false;CreateSessionNow();return;}
		if(bWasLeaving)OnLeaveCrewSessionComplete.Broadcast(true,FString());
		return;
	}
	bRecreateAfterDestroy=false;
	if(bWasLeaving)OnLeaveCrewSessionComplete.Broadcast(false,TEXT("The crew session could not be closed."));
	else OnHostSessionComplete.Broadcast(false,TEXT("The previous crew session could not be closed."));
}

void UMultiplayerSessionSubsystem::FindAndJoinCrewSession(bool bIsLAN)
{
	if(!SessionInterface.IsValid()){OnJoinCrewSessionComplete.Broadcast(false,TEXT("Online session provider is unavailable."));return;}
	SessionSearch=MakeShared<FOnlineSessionSearch>();SessionSearch->bIsLanQuery=bIsLAN;SessionSearch->MaxSearchResults=50;SessionSearch->PingBucketSize=50;
	FindDelegateHandle=SessionInterface->AddOnFindSessionsCompleteDelegate_Handle(FOnFindSessionsCompleteDelegate::CreateUObject(this,&UMultiplayerSessionSubsystem::HandleFindSessionsComplete));
	if(!SessionInterface->FindSessions(0,SessionSearch.ToSharedRef())){SessionInterface->ClearOnFindSessionsCompleteDelegate_Handle(FindDelegateHandle);FindDelegateHandle.Reset();SessionSearch.Reset();OnJoinCrewSessionComplete.Broadcast(false,TEXT("Crew search could not be started."));}
}

void UMultiplayerSessionSubsystem::HandleFindSessionsComplete(bool bWasSuccessful)
{
	if(SessionInterface.IsValid())SessionInterface->ClearOnFindSessionsCompleteDelegate_Handle(FindDelegateHandle);FindDelegateHandle.Reset();
	if(!bWasSuccessful||!SessionSearch.IsValid()){OnJoinCrewSessionComplete.Broadcast(false,TEXT("Crew search failed."));return;}
	const FOnlineSessionSearchResult* Match=nullptr;
	for(const FOnlineSessionSearchResult& Result:SessionSearch->SearchResults)
	{
		FString Build;Result.Session.SessionSettings.Get(FName(TEXT("GINNUNGAGAP_BUILD")),Build);
		if(Build==TEXT("prototype-01")&&Result.Session.NumOpenPublicConnections>0){Match=&Result;break;}
	}
	if(!Match){OnJoinCrewSessionComplete.Broadcast(false,TEXT("No compatible crew sessions were found."));return;}
	JoinDelegateHandle=SessionInterface->AddOnJoinSessionCompleteDelegate_Handle(FOnJoinSessionCompleteDelegate::CreateUObject(this,&UMultiplayerSessionSubsystem::HandleJoinSessionComplete));
	if(!SessionInterface->JoinSession(0,NAME_GameSession,*Match)){SessionInterface->ClearOnJoinSessionCompleteDelegate_Handle(JoinDelegateHandle);JoinDelegateHandle.Reset();OnJoinCrewSessionComplete.Broadcast(false,TEXT("The selected crew session could not be joined."));}
}

void UMultiplayerSessionSubsystem::HandleJoinSessionComplete(FName SessionName,EOnJoinSessionCompleteResult::Type Result)
{
	if(SessionInterface.IsValid())SessionInterface->ClearOnJoinSessionCompleteDelegate_Handle(JoinDelegateHandle);JoinDelegateHandle.Reset();
	if(Result!=EOnJoinSessionCompleteResult::Success||!SessionInterface.IsValid()){OnJoinCrewSessionComplete.Broadcast(false,TEXT("The host rejected the crew connection."));return;}
	FString Address;if(!SessionInterface->GetResolvedConnectString(SessionName,Address)||Address.IsEmpty()){OnJoinCrewSessionComplete.Broadcast(false,TEXT("The host address could not be resolved."));return;}
	if(UGameInstance* GI=GetGameInstance())if(APlayerController* PC=GI->GetFirstLocalPlayerController()){bSessionActive=true;bIsHost=false;OnJoinCrewSessionComplete.Broadcast(true,FString());PC->ClientTravel(Address,ETravelType::TRAVEL_Absolute);return;}
	OnJoinCrewSessionComplete.Broadcast(false,TEXT("No local player was available for travel."));
}

void UMultiplayerSessionSubsystem::HandleNetworkFailure(UWorld* World,UNetDriver* NetDriver,ENetworkFailure::Type FailureType,const FString& ErrorString)
{
	if(bSessionActive)RecoverFromConnectionFailure(ErrorString.IsEmpty()?TEXT("The crew connection was lost."):ErrorString);
}

void UMultiplayerSessionSubsystem::HandleTravelFailure(UWorld* World,ETravelFailure::Type FailureType,const FString& ErrorString)
{
	if(bSessionActive)RecoverFromConnectionFailure(ErrorString.IsEmpty()?TEXT("The crew could not travel to the expedition."):ErrorString);
}

void UMultiplayerSessionSubsystem::RecoverFromConnectionFailure(const FString& ErrorString)
{
	bSessionActive=false;bIsHost=false;bLeavingSession=false;bRecreateAfterDestroy=false;
	if(SessionInterface.IsValid()&&SessionInterface->GetNamedSession(NAME_GameSession))SessionInterface->DestroySession(NAME_GameSession);
	OnCrewConnectionLost.Broadcast(ErrorString.Left(160));
}
