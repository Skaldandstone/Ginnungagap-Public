#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Interfaces/OnlineSessionInterface.h"
#include "MultiplayerSessionSubsystem.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnHostSessionComplete, bool, bSuccess, const FString&, ErrorMessage);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnJoinCrewSessionComplete, bool, bSuccess, const FString&, ErrorMessage);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnLeaveCrewSessionComplete, bool, bSuccess, const FString&, ErrorMessage);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCrewConnectionLost, const FString&, ErrorMessage);

UCLASS()
class GINNUNGAGAP_API UMultiplayerSessionSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()
public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	UFUNCTION(BlueprintCallable, Category="Multiplayer") void HostSession(int32 PublicConnections,const FString& MapName,bool bIsLAN=true);
	UFUNCTION(BlueprintCallable, Category="Multiplayer") void FindAndJoinCrewSession(bool bIsLAN=true);
	UFUNCTION(BlueprintCallable, Category="Multiplayer") void LeaveCrewSession();
	UFUNCTION(BlueprintPure, Category="Multiplayer") bool HasHostedSession() const{return bSessionActive;}
	UFUNCTION(BlueprintPure, Category="Multiplayer") bool IsInCrewSession() const{return bSessionActive;}
	UFUNCTION(BlueprintPure, Category="Multiplayer") bool IsCrewHost() const{return bSessionActive&&bIsHost;}
	UPROPERTY(BlueprintAssignable, Category="Multiplayer") FOnHostSessionComplete OnHostSessionComplete;
	UPROPERTY(BlueprintAssignable, Category="Multiplayer") FOnJoinCrewSessionComplete OnJoinCrewSessionComplete;
	UPROPERTY(BlueprintAssignable, Category="Multiplayer") FOnLeaveCrewSessionComplete OnLeaveCrewSessionComplete;
	UPROPERTY(BlueprintAssignable, Category="Multiplayer") FOnCrewConnectionLost OnCrewConnectionLost;
private:
	void CreateSessionNow();
	void HandleCreateSessionComplete(FName SessionName,bool bWasSuccessful);
	void HandleDestroySessionComplete(FName SessionName,bool bWasSuccessful);
	void HandleFindSessionsComplete(bool bWasSuccessful);
	void HandleJoinSessionComplete(FName SessionName,EOnJoinSessionCompleteResult::Type Result);
	void HandleNetworkFailure(UWorld* World, class UNetDriver* NetDriver, ENetworkFailure::Type FailureType, const FString& ErrorString);
	void HandleTravelFailure(UWorld* World, ETravelFailure::Type FailureType, const FString& ErrorString);
	void RecoverFromConnectionFailure(const FString& ErrorString);
	IOnlineSessionPtr SessionInterface;
	FDelegateHandle CreateDelegateHandle;
	FDelegateHandle DestroyDelegateHandle;
	FDelegateHandle FindDelegateHandle;
	FDelegateHandle JoinDelegateHandle;
	FDelegateHandle NetworkFailureHandle;
	FDelegateHandle TravelFailureHandle;
	TSharedPtr<FOnlineSessionSearch> SessionSearch;
	int32 PendingConnections=4;
	FString PendingMapName;
	bool bPendingLAN=true;
	bool bSessionActive=false;
	bool bIsHost=false;
	bool bRecreateAfterDestroy=false;
	bool bLeavingSession=false;
};
