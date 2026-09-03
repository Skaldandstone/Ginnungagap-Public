#include "UI/MapCustomizationWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/SafeZone.h"
#include "UI/MenuVisualStyle.h"
#include "Input/Reply.h"

void UMapCustomizationWidget::NativeConstruct()
{
	Super::NativeConstruct();
	BuildFallbackLayout();

	// Bind combo box events
	if (ShipSizeCombo)
	{
		ShipSizeCombo->OnSelectionChanged.AddDynamic(this, &UMapCustomizationWidget::OnShipSizeChanged);
	}

	if (DifficultyCombo)
	{
		DifficultyCombo->OnSelectionChanged.AddDynamic(this, &UMapCustomizationWidget::OnDifficultyChanged);
	}

	if (MapCombo)
	{
		MapCombo->OnSelectionChanged.AddDynamic(this, &UMapCustomizationWidget::OnMapChanged);
	}
	if (ProtagonistSlotsCombo) ProtagonistSlotsCombo->OnSelectionChanged.AddDynamic(this, &UMapCustomizationWidget::OnProtagonistSlotsChanged);
	if (AntagonistSlotsCombo) AntagonistSlotsCombo->OnSelectionChanged.AddDynamic(this, &UMapCustomizationWidget::OnAntagonistSlotsChanged);
	if (AntagonistFactionCombo) AntagonistFactionCombo->OnSelectionChanged.AddDynamic(this, &UMapCustomizationWidget::OnAntagonistFactionChanged);
	if (IndependentAICombo) IndependentAICombo->OnSelectionChanged.AddDynamic(this, &UMapCustomizationWidget::OnIndependentAIChanged);

	// Bind buttons
	if (StartGameButton)
	{
		StartGameButton->OnClicked.AddDynamic(this, &UMapCustomizationWidget::OnStartGameClicked);
	}

	if (BackButton)
	{
		BackButton->OnClicked.AddDynamic(this, &UMapCustomizationWidget::OnBackClicked);
	}

	PopulateDropdowns();
	UpdateDescriptions();
	SetIsFocusable(true);
	if (ShipSizeCombo) ShipSizeCombo->SetKeyboardFocus();
}

FReply UMapCustomizationWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape || InKeyEvent.GetKey() == EKeys::Gamepad_Special_Left || InKeyEvent.GetKey() == EKeys::Gamepad_FaceButton_Right)
	{
		OnBackClicked();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UMapCustomizationWidget::NativeDestruct()
{
	if (ShipSizeCombo) ShipSizeCombo->OnSelectionChanged.RemoveDynamic(this, &UMapCustomizationWidget::OnShipSizeChanged);
	if (DifficultyCombo) DifficultyCombo->OnSelectionChanged.RemoveDynamic(this, &UMapCustomizationWidget::OnDifficultyChanged);
	if (MapCombo) MapCombo->OnSelectionChanged.RemoveDynamic(this, &UMapCustomizationWidget::OnMapChanged);
	if (ProtagonistSlotsCombo) ProtagonistSlotsCombo->OnSelectionChanged.RemoveDynamic(this, &UMapCustomizationWidget::OnProtagonistSlotsChanged);
	if (AntagonistSlotsCombo) AntagonistSlotsCombo->OnSelectionChanged.RemoveDynamic(this, &UMapCustomizationWidget::OnAntagonistSlotsChanged);
	if (AntagonistFactionCombo) AntagonistFactionCombo->OnSelectionChanged.RemoveDynamic(this, &UMapCustomizationWidget::OnAntagonistFactionChanged);
	if (IndependentAICombo) IndependentAICombo->OnSelectionChanged.RemoveDynamic(this, &UMapCustomizationWidget::OnIndependentAIChanged);
	if (StartGameButton) StartGameButton->OnClicked.RemoveDynamic(this, &UMapCustomizationWidget::OnStartGameClicked);
	if (BackButton) BackButton->OnClicked.RemoveDynamic(this, &UMapCustomizationWidget::OnBackClicked);
	Super::NativeDestruct();
}

void UMapCustomizationWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("CustomizationRoot"));
	GinnungagapMenuStyle::ApplyTerminalPanel(Root); Root->SetPadding(FMargin(110, 68)); USafeZone* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass(),TEXT("SafeZone"));Safe->AddChild(Root);WidgetTree->RootWidget=Safe;
	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Root->SetContent(Stack);
	auto AddLabel = [this, Stack](const TCHAR* Name, const TCHAR* Copy, int32 Size, FLinearColor Color)
	{
		UTextBlock* T = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name); T->SetText(FText::FromString(Copy));
		GinnungagapMenuStyle::ApplyTerminalText(T,Size,Color,Size<=12); Stack->AddChildToVerticalBox(T); return T;
	};
	AddLabel(TEXT("StepText"), TEXT("DERELICT CONTROL  //  WAKE PROTOCOL 02 OF 03"), 12, GinnungagapMenuStyle::SafetyAmber);
	UTextBlock* Heading = AddLabel(TEXT("HeadingText"), TEXT("CONFIGURE WAKE CONDITIONS"), 36, GinnungagapMenuStyle::CryoWhite);
	if (UVerticalBoxSlot* HeadingSlot = Cast<UVerticalBoxSlot>(Heading->Slot)) HeadingSlot->SetPadding(FMargin(0, 12, 0, 42));
	auto AddChoice = [this, Stack](const TCHAR* Label, const TCHAR* ComboName, UComboBoxString*& Combo, const TCHAR* DescName, UTextBlock*& Desc)
	{
		UTextBlock* L = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()); L->SetText(FText::FromString(Label));
		GinnungagapMenuStyle::ApplyTerminalText(L,12,GinnungagapMenuStyle::SafetyAmber,true); Stack->AddChildToVerticalBox(L);
		Combo = WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(), ComboName);
		if (UVerticalBoxSlot* ComboSlot = Stack->AddChildToVerticalBox(Combo)) ComboSlot->SetPadding(FMargin(0, 8, 0, 8));
		Desc = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), DescName); Desc->SetAutoWrapText(true);
		GinnungagapMenuStyle::ApplyTerminalText(Desc,12,GinnungagapMenuStyle::MutedSteel);
		if (UVerticalBoxSlot* DescSlot = Stack->AddChildToVerticalBox(Desc)) DescSlot->SetPadding(FMargin(0, 0, 0, 24));
	};
	AddChoice(TEXT("VESSEL"), TEXT("ShipSizeCombo"), ShipSizeCombo, TEXT("ShipSizeDescriptionText"), ShipSizeDescriptionText);
	AddChoice(TEXT("THREAT PROFILE"), TEXT("DifficultyCombo"), DifficultyCombo, TEXT("DifficultyDescriptionText"), DifficultyDescriptionText);
	UTextBlock* MapLabel = AddLabel(TEXT("MapLabel"), TEXT("DERELICT SIGNAL ORIGIN"), 12, GinnungagapMenuStyle::SafetyAmber);
	if (UVerticalBoxSlot* MapLabelSlot = Cast<UVerticalBoxSlot>(MapLabel->Slot)) MapLabelSlot->SetPadding(FMargin(0, 0, 0, 8));
	MapCombo = WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(), TEXT("MapCombo")); Stack->AddChildToVerticalBox(MapCombo);
	if (SelectedGameMode == EGameMode::Versus)
	{
		UTextBlock* VersusLabel = AddLabel(TEXT("VersusLabel"), TEXT("CONTAINMENT FAILURE PARAMETERS"), 12, GinnungagapMenuStyle::FaultRed);
		if (UVerticalBoxSlot* LabelSlot = Cast<UVerticalBoxSlot>(VersusLabel->Slot)) LabelSlot->SetPadding(FMargin(0, 24, 0, 8));
		ProtagonistSlotsCombo = WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(), TEXT("ProtagonistSlotsCombo"));
		AntagonistSlotsCombo = WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(), TEXT("AntagonistSlotsCombo"));
		AntagonistFactionCombo = WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(), TEXT("AntagonistFactionCombo"));
		IndependentAICombo = WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(), TEXT("IndependentAICombo"));
		Stack->AddChildToVerticalBox(ProtagonistSlotsCombo);
		Stack->AddChildToVerticalBox(AntagonistSlotsCombo);
		Stack->AddChildToVerticalBox(AntagonistFactionCombo);
		Stack->AddChildToVerticalBox(IndependentAICombo);
	}
	UHorizontalBox* Actions = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	if (UVerticalBoxSlot* ActionSlot = Stack->AddChildToVerticalBox(Actions)) ActionSlot->SetPadding(FMargin(0, 42, 0, 0));
	auto Action = [this, Actions](const TCHAR* Name, const TCHAR* Copy, UButton*& Button, FLinearColor Color)
	{
		Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name); Button->SetBackgroundColor(Color);
		GinnungagapMenuStyle::ApplyButton(Button,FString(Name).Contains(TEXT("Start")));
		UTextBlock* T = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()); T->SetText(FText::FromString(Copy));
		T->SetColorAndOpacity(FSlateColor(FLinearColor(0.9f, 0.95f, 0.96f))); Button->AddChild(T); Actions->AddChildToHorizontalBox(Button);
	};
	Action(TEXT("BackButton"), TEXT("<  BACK"), BackButton, FLinearColor(0.05f, 0.08f, 0.09f));
	Action(TEXT("StartGameButton"), TEXT("CONFIRM & DEPLOY  >"), StartGameButton, FLinearColor(0.02f, 0.34f, 0.42f));
}

void UMapCustomizationWidget::SetIsCoopMode(bool bInIsCoopMode)
{
	bIsCoopMode = bInIsCoopMode;
}

void UMapCustomizationWidget::SetGameMode(EGameMode InGameMode)
{
	SelectedGameMode = InGameMode;
	bIsCoopMode = InGameMode != EGameMode::SinglePlayerSurvival;
}

void UMapCustomizationWidget::PopulateDropdowns()
{
	// The four-deck authored ship is intentionally the only vessel exposed while
	// this vertical slice is being built out.
	if (ShipSizeCombo)
	{
		ShipSizeCombo->ClearOptions();
		ShipSizeCombo->AddOption(TEXT("GINNUNGAGAP // FOUR-DECK PROTOTYPE"));
		ShipSizeCombo->SetSelectedIndex(0);
		ShipSizeCombo->SetIsEnabled(false);
		ShipSizeCombo->SetToolTipText(FText::FromString(TEXT("Only the four-deck prototype is deployable in this build.")));
		CurrentCustomization.ShipSize = EShipSize::Medium;
	}

	// Populate difficulty options
	if (DifficultyCombo)
	{
		DifficultyCombo->ClearOptions();
		DifficultyCombo->AddOption(TEXT("Easy"));
		DifficultyCombo->AddOption(TEXT("Normal"));
		DifficultyCombo->AddOption(TEXT("Hard"));
		DifficultyCombo->AddOption(TEXT("Impossible"));
		DifficultyCombo->SetSelectedIndex(1); // Default to Normal
	}

	// Populate map options
	if (MapCombo)
	{
		MapCombo->ClearOptions();
		RefreshDeploymentSite();
	}

	if (ProtagonistSlotsCombo)
	{
		for (int32 Count = 1; Count <= 8; ++Count) ProtagonistSlotsCombo->AddOption(FString::Printf(TEXT("Crew: %d"), Count));
		ProtagonistSlotsCombo->SetSelectedIndex(CurrentCustomization.VersusSettings.ProtagonistSlots - 1);
	}
	if (AntagonistSlotsCombo)
	{
		for (int32 Count = 1; Count <= 4; ++Count) AntagonistSlotsCombo->AddOption(FString::Printf(TEXT("Antagonists: %d"), Count));
		AntagonistSlotsCombo->SetSelectedIndex(CurrentCustomization.VersusSettings.AntagonistSlots - 1);
	}
	if (AntagonistFactionCombo)
	{
		AntagonistFactionCombo->AddOption(TEXT("Bloom"));
		AntagonistFactionCombo->AddOption(TEXT("Pirates"));
		AntagonistFactionCombo->AddOption(TEXT("Rebels"));
		AntagonistFactionCombo->AddOption(TEXT("Alien"));
		AntagonistFactionCombo->SetSelectedOption(TEXT("Bloom"));
	}
	if (IndependentAICombo)
	{
		IndependentAICombo->AddOption(TEXT("No independent faction"));
		IndependentAICombo->AddOption(TEXT("AI Pirates"));
		IndependentAICombo->AddOption(TEXT("AI Rebels"));
		IndependentAICombo->AddOption(TEXT("AI Alien"));
		IndependentAICombo->SetSelectedIndex(0);
	}
}

void UMapCustomizationWidget::OnShipSizeChanged(FString SelectedItem, ESelectInfo::Type SelectionType)
{
	CurrentCustomization.ShipSize = EShipSize::Medium;

	RefreshDeploymentSite();
	UpdateDescriptions();
}

void UMapCustomizationWidget::OnDifficultyChanged(FString SelectedItem, ESelectInfo::Type SelectionType)
{
	if (SelectedItem == TEXT("Easy"))
	{
		CurrentCustomization.Difficulty = EGameDifficulty::Easy;
	}
	else if (SelectedItem == TEXT("Normal"))
	{
		CurrentCustomization.Difficulty = EGameDifficulty::Normal;
	}
	else if (SelectedItem == TEXT("Hard"))
	{
		CurrentCustomization.Difficulty = EGameDifficulty::Hard;
	}
	else if (SelectedItem == TEXT("Impossible"))
	{
		CurrentCustomization.Difficulty = EGameDifficulty::Impossible;
	}

	UpdateDescriptions();
}

void UMapCustomizationWidget::OnMapChanged(FString SelectedItem, ESelectInfo::Type SelectionType)
{
	CurrentCustomization.SelectedMap = SelectedItem;
}

void UMapCustomizationWidget::OnProtagonistSlotsChanged(FString SelectedItem, ESelectInfo::Type SelectionType)
{
	CurrentCustomization.VersusSettings.ProtagonistSlots =
		FMath::Clamp(FCString::Atoi(*SelectedItem.RightChop(6)), 1, 8);
}

void UMapCustomizationWidget::OnAntagonistSlotsChanged(FString SelectedItem, ESelectInfo::Type SelectionType)
{
	CurrentCustomization.VersusSettings.AntagonistSlots =
		FMath::Clamp(FCString::Atoi(*SelectedItem.RightChop(13)), 1, 4);
}

void UMapCustomizationWidget::OnAntagonistFactionChanged(FString SelectedItem, ESelectInfo::Type SelectionType)
{
	if (SelectedItem == TEXT("Pirates")) CurrentCustomization.VersusSettings.PlayerAntagonistFaction = EAntagonistFaction::Pirates;
	else if (SelectedItem == TEXT("Rebels")) CurrentCustomization.VersusSettings.PlayerAntagonistFaction = EAntagonistFaction::Rebels;
	else if (SelectedItem == TEXT("Alien")) CurrentCustomization.VersusSettings.PlayerAntagonistFaction = EAntagonistFaction::Alien;
	else CurrentCustomization.VersusSettings.PlayerAntagonistFaction = EAntagonistFaction::Bloom;
	CurrentCustomization.VersusSettings.Sanitize();
}

void UMapCustomizationWidget::OnIndependentAIChanged(FString SelectedItem, ESelectInfo::Type SelectionType)
{
	CurrentCustomization.VersusSettings.IndependentAIFactions.Reset();
	if (SelectedItem == TEXT("AI Pirates")) CurrentCustomization.VersusSettings.IndependentAIFactions.Add(EAntagonistFaction::Pirates);
	else if (SelectedItem == TEXT("AI Rebels")) CurrentCustomization.VersusSettings.IndependentAIFactions.Add(EAntagonistFaction::Rebels);
	else if (SelectedItem == TEXT("AI Alien")) CurrentCustomization.VersusSettings.IndependentAIFactions.Add(EAntagonistFaction::Alien);
	CurrentCustomization.VersusSettings.Sanitize();
}

void UMapCustomizationWidget::UpdateDescriptions()
{
	// Update ship size description
	if (ShipSizeDescriptionText)
	{
		ShipSizeDescriptionText->SetText(FText::FromString(MediumShipDesc));
	}

	// Update difficulty description
	if (DifficultyDescriptionText)
	{
		FString Desc;
		switch (CurrentCustomization.Difficulty)
		{
			case EGameDifficulty::Easy:
				Desc = EasyDesc;
				break;
			case EGameDifficulty::Normal:
				Desc = NormalDesc;
				break;
			case EGameDifficulty::Hard:
				Desc = HardDesc;
				break;
			case EGameDifficulty::Impossible:
				Desc = ImpossibleDesc;
				break;
		}
		DifficultyDescriptionText->SetText(FText::FromString(Desc));
	}
}

void UMapCustomizationWidget::OnStartGameClicked()
{
	if (bLaunchRequested) return;
	bLaunchRequested = true;
	if (StartGameButton)
	{
		StartGameButton->SetIsEnabled(false);
		StartGameButton->SetToolTipText(FText::FromString(TEXT("Preparing expedition...")));
	}
	OnGameStarted.Broadcast();
}

void UMapCustomizationWidget::OnBackClicked()
{
	OnBackRequested.Broadcast();
}

void UMapCustomizationWidget::RefreshDeploymentSite()
{
	if (!MapCombo) return;
	MapCombo->ClearOptions();
	const FString Site = TEXT("DERELICT SHIP // FOUR-DECK QUICK DEMO");
	MapCombo->AddOption(Site);
	MapCombo->SetSelectedIndex(0);
	CurrentCustomization.SelectedMap = Site;
	MapCombo->SetIsEnabled(false);
	MapCombo->SetToolTipText(FText::FromString(TEXT("This is the only deployment site enabled while the prototype ship is being built.")));
}
