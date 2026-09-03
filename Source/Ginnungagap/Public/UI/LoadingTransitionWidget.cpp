#include "UI/LoadingTransitionWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/SafeZone.h"

void ULoadingTransitionWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized(); BuildFallbackLayout(); ElapsedSeconds = 0.0f; RefreshText();
}

void ULoadingTransitionWidget::NativeConstruct()
{
	Super::NativeConstruct();
	// Focus needs the Slate tree, which exists only once the widget is constructed.
}

void ULoadingTransitionWidget::Configure(const FCharacterProfile& Character, const FGameCustomization& Customization, EGameMode GameMode)
{
	CharacterProfile = Character; GameCustomization = Customization; SelectedMode = GameMode; RefreshText();
}

void ULoadingTransitionWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
	Super::NativeTick(Geometry, DeltaSeconds); ElapsedSeconds += DeltaSeconds;
	if (StatusText)
	{
		const int32 Dots = 1 + (FMath::FloorToInt(ElapsedSeconds * 2.5f) % 3);
		StatusText->SetText(FText::FromString(FString::Printf(TEXT("INITIALIZING DEPLOYMENT%.*s"), Dots, TEXT("..."))));
	}
}

void ULoadingTransitionWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("LoadingRoot"));
	Root->SetBrushColor(FLinearColor(0.003f,0.008f,0.012f,1)); Root->SetPadding(FMargin(100,70)); USafeZone* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass(),TEXT("SafeZone"));Safe->AddChild(Root);WidgetTree->RootWidget=Safe;
	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(); Root->SetContent(Stack);
	auto AddText=[this,Stack](const TCHAR* Name,const TCHAR* Copy,int32 Size,FLinearColor Color){UTextBlock* T=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),Name);T->SetText(FText::FromString(Copy));T->SetFont(FSlateFontInfo(T->GetFont().FontObject,Size));T->SetColorAndOpacity(FSlateColor(Color));T->SetAutoWrapText(true);Stack->AddChildToVerticalBox(T);return T;};
	AddText(TEXT("KickerText"),TEXT("EXPEDITION CONTROL  //  DEPLOYMENT BRIEF"),12,FLinearColor(0.30f,0.86f,1));
	UTextBlock* Heading=AddText(TEXT("HeadingText"),TEXT("PREPARING EXPEDITION"),38,FLinearColor(0.88f,0.94f,0.95f));
	if(UVerticalBoxSlot* S=Cast<UVerticalBoxSlot>(Heading->Slot))S->SetPadding(FMargin(0,14,0,60));
	CharacterText=AddText(TEXT("CharacterText"),TEXT(""),18,FLinearColor(0.88f,0.94f,0.95f));
	if(UVerticalBoxSlot* S=Cast<UVerticalBoxSlot>(CharacterText->Slot))S->SetPadding(FMargin(0,0,0,18));
	ExpeditionText=AddText(TEXT("ExpeditionText"),TEXT(""),15,FLinearColor(0.48f,0.58f,0.62f));
	USpacer* Fill=WidgetTree->ConstructWidget<USpacer>(); Fill->SetSize(FVector2D(1,180)); Stack->AddChildToVerticalBox(Fill);
	StatusText=AddText(TEXT("StatusText"),TEXT("INITIALIZING DEPLOYMENT..."),13,FLinearColor(0.30f,0.86f,1));
	AddText(TEXT("HintText"),TEXT("VERIFYING CREW PROFILE  //  PRESSURE SEALS  //  LIFE SUPPORT  //  MISSION DATA"),11,FLinearColor(0.32f,0.40f,0.43f));
}

void ULoadingTransitionWidget::RefreshText()
{
	const UEnum* RoleEnum=StaticEnum<EPressureSuitRole>(); const UEnum* ShipEnum=StaticEnum<EShipSize>(); const UEnum* DifficultyEnum=StaticEnum<EGameDifficulty>(); const UEnum* ModeEnum=StaticEnum<EGameMode>();
	if(CharacterText)CharacterText->SetText(FText::FromString(FString::Printf(TEXT("%s  //  %s OPERATOR"),*CharacterProfile.CharacterName.ToUpper(),RoleEnum?*RoleEnum->GetDisplayNameTextByValue(static_cast<int64>(CharacterProfile.SuitRole)).ToString().ToUpper():TEXT("CREW"))));
	if(ExpeditionText)ExpeditionText->SetText(FText::FromString(FString::Printf(TEXT("%s  //  %s VESSEL  //  %s THREAT\n%s"),ModeEnum?*ModeEnum->GetDisplayNameTextByValue(static_cast<int64>(SelectedMode)).ToString().ToUpper():TEXT("EXPEDITION"),ShipEnum?*ShipEnum->GetDisplayNameTextByValue(static_cast<int64>(GameCustomization.ShipSize)).ToString().ToUpper():TEXT("MEDIUM"),DifficultyEnum?*DifficultyEnum->GetDisplayNameTextByValue(static_cast<int64>(GameCustomization.Difficulty)).ToString().ToUpper():TEXT("NORMAL"),*GameCustomization.SelectedMap)));
}
