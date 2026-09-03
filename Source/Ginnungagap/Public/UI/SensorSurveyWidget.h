#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "StarSystem/StarSystemTypes.h"
#include "SensorSurveyWidget.generated.h"

class ASensorArraySystem;
class UScrollBox;
class UTextBlock;
class UButton;
class AShipHelmSystem;
class UShipResourceInventorySubsystem;
enum class EStarSystemResourceType : uint8;

/** Native fallback survey display; Blueprint subclasses can replace its presentation later. */
UCLASS()
class GINNUNGAGAP_API USensorSurveyWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
    virtual void NativeDestruct() override;

    UFUNCTION(BlueprintCallable, Category = "Sensors")
    void SetSensorSource(ASensorArraySystem* InSensorSource);

    UFUNCTION(BlueprintCallable, Category = "Sensors")
    void RefreshContacts();

    UFUNCTION(BlueprintCallable, Category = "Sensors|Operations")
    bool DispatchDroneOperation();

    UFUNCTION(BlueprintCallable, Category = "Sensors|Operations")
    bool PerformEVAOperation();

    UFUNCTION(BlueprintCallable, Category = "Sensors|Operations")
    bool PerformCollectorOperation();

    /** Shared policy used by native UI actions and automation coverage. */
    static bool CanExecuteDirectResourceOperation(EResourceAcquisitionMethod Method,
        bool bShipOnStation, bool bAcquisitionRequirementSatisfied);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sensors")
    float RefreshInterval = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sensors|Navigation", meta = (ClampMin = "1"))
    int32 HeadingCorrectionFuelCost = 10;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sensors|Navigation", meta = (ClampMin = "0.0"))
    float HeadingCorrectionThresholdDegrees = 5.0f;

private:
    void BuildWidgetTree();

    UPROPERTY()
    TObjectPtr<ASensorArraySystem> SensorSource;

    UPROPERTY()
    TObjectPtr<UScrollBox> ContactList;

    UPROPERTY()
    TObjectPtr<UTextBlock> StatusText;

    UPROPERTY()
    TObjectPtr<UTextBlock> SystemIdentityText;

    UPROPERTY()
    TObjectPtr<UTextBlock> OperationsText;

    UPROPERTY()
    TObjectPtr<UButton> DispatchDroneButton;

    UPROPERTY()
    TObjectPtr<UButton> EVAOperationButton;

    UPROPERTY()
    TObjectPtr<UButton> CollectorOperationButton;

    UPROPERTY()
    TObjectPtr<UTextBlock> CollectorOperationLabel;

    UPROPERTY()
    TObjectPtr<UButton> TrackPriorityButton;

    UPROPERTY()
    TObjectPtr<UButton> HeadingAssistButton;

    UPROPERTY()
    TObjectPtr<UTextBlock> HeadingAssistLabel;

    UPROPERTY()
    TObjectPtr<UTextBlock> CoursePreviewText;

    UPROPERTY()
    TObjectPtr<UButton> HeadingCorrectionButton;

    UPROPERTY()
    TObjectPtr<UTextBlock> DroneStatusText;

    UPROPERTY()
    TObjectPtr<UTextBlock> InventoryText;

    UPROPERTY()
    TObjectPtr<UTextBlock> ResourceResultText;

    UPROPERTY()
    TObjectPtr<UShipResourceInventorySubsystem> CachedInventory;

    UPROPERTY()
    TObjectPtr<AShipHelmSystem> CachedHelm;

    UFUNCTION()
    void HandleDispatchDroneClicked();

    UFUNCTION()
    void HandleEVAOperationClicked();

    UFUNCTION()
    void HandleCollectorOperationClicked();

    UFUNCTION()
    void HandleTrackPriorityClicked();

    UFUNCTION()
    void HandleHeadingAssistClicked();

    UFUNCTION()
    void HandleHeadingCorrectionClicked();

    UFUNCTION()
    void HandleResourceChanged(EStarSystemResourceType ResourceType, int32 NewAmount, int32 Delta);

    void RefreshInventoryDisplay();

    float RefreshAccumulator = 0.0f;
};
