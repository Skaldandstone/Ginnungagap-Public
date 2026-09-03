#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "BootSplashWidget.generated.h"

class UBorder;
class UTextBlock;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnBootSplashFinished);

/** Short, skippable startup beat shown once before the title gate. */
UCLASS()
class GINNUNGAGAP_API UBootSplashWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;

	UPROPERTY(BlueprintAssignable, Category="Boot")
	FOnBootSplashFinished OnFinished;

protected:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Boot", meta=(ClampMin="0.5"))
	float MinimumDisplaySeconds = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Boot", meta=(ClampMin="1.0"))
	float AutomaticAdvanceSeconds = 3.0f;

private:
	void BuildFallbackLayout();
	void RequestSkip();
	void Complete();

	UPROPERTY(Transient)
	TObjectPtr<UBorder> IdentityPanel;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> SkipText;

	float ElapsedSeconds = 0.0f;
	bool bSkipRequested = false;
	bool bCompleted = false;
};
