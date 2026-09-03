#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Ship/SensorArraySystem.h"
#include "SensorContactRowWidget.generated.h"

class UButton;
class UTextBlock;

UCLASS()
class GINNUNGAGAP_API USensorContactRowWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeOnInitialized() override;
    virtual void NativeConstruct() override;

    void Configure(ASensorArraySystem* InSensorSource, const FSensorContact& InContact, bool bIsTracked);

private:
    UFUNCTION()
    void HandleClicked();

    void RefreshLabel();

    UPROPERTY()
    TObjectPtr<ASensorArraySystem> SensorSource;

    UPROPERTY()
    TObjectPtr<UButton> SelectButton;

    UPROPERTY()
    TObjectPtr<UTextBlock> Label;

    FSensorContact Contact;
    bool bTracked = false;
};
