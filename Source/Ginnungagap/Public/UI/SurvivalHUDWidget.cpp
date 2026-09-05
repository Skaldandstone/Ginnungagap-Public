// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/SurvivalHUDWidget.h"
#include "Public/CoopSurvivalCharacter.h"
#include "Interaction/InteractionComponent.h"
#include "Interfaces/Interactable.h"
#include "Interaction/BioScannerComponent.h"
#include "Activities/PlayerActivityComponent.h"
#include "Activities/ActivityStation.h"
#include "UI/ActivityMinigameWidget.h"
#include "UI/SkillAbilityBarWidget.h"
#include "Public/StarSystem/JumpSequenceSubsystem.h"
#include "Public/Meta/RunOutcomeSubsystem.h"
#include "Public/Meta/CharacterProfileSubsystem.h"
#include "Public/Ship/ArmorPlatingSystem.h"
#include "Public/Ship/SensorArraySystem.h"
#include "Public/Ship/ShipHelmSystem.h"
#include "Public/Ship/ShipPropulsionSubsystem.h"
#include "Public/Ship/ShipSystemActor.h"
#include "Mission/MissionObjectiveSubsystem.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "StatusEffects/PlayerPsychosisComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/ScaleBox.h"
#include "Components/SizeBox.h"

namespace
{
    const FLinearColor HudCyan(0.18f, 0.78f, 0.92f, 0.92f);
    const FLinearColor HudCyanDim(0.10f, 0.42f, 0.52f, 0.58f);
    const FLinearColor HudAmber(1.0f, 0.58f, 0.08f, 0.96f);
    const FLinearColor HudPanel(0.005f, 0.025f, 0.035f, 0.68f);

    UCanvasPanelSlot* AnchorTopLeft(UPanelWidget* Parent, UWidget* Child, const FVector2D& Position, const FVector2D& Size)
    {
        UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(Parent->AddChild(Child));
        if (Slot)
        {
            Slot->SetAnchors(FAnchors(0.0f, 0.0f));
            Slot->SetAlignment(FVector2D(0.0f, 0.0f));
            Slot->SetPosition(Position);
            Slot->SetSize(Size);
        }
        return Slot;
    }

    UBorder* AddHudPanel(UWidgetTree* WidgetTree, UCanvasPanel* Root, const TCHAR* Name,
        const FVector2D& Position, const FVector2D& Size)
    {
        UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), Name);
        Panel->SetBrushColor(HudPanel);
        Panel->SetPadding(FMargin(8.0f));
        Panel->SetVisibility(ESlateVisibility::HitTestInvisible);
        AnchorTopLeft(Root, Panel, Position, Size);
        return Panel;
    }
}

void USurvivalHUDWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();

    BuildWidgetTree();

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UCharacterProfileSubsystem* ProfileSubsystem = GI->GetSubsystem<UCharacterProfileSubsystem>())
        {
            SetCharacterName(ProfileSubsystem->GetCharacterName());
            ProfileSubsystem->OnCharacterProfileChanged.AddDynamic(this, &USurvivalHUDWidget::OnCharacterProfileChanged);
        }
    }
}

void USurvivalHUDWidget::NativeConstruct()
{
    Super::NativeConstruct();
    // Focus needs the Slate tree, which exists only once the widget is constructed.
}

void USurvivalHUDWidget::BuildWidgetTree()
{
    if (!WidgetTree)
    {
        return;
    }

    UScaleBox* ViewportScaler = WidgetTree->ConstructWidget<UScaleBox>(UScaleBox::StaticClass(), TEXT("ViewportScaler"));
    ViewportScaler->SetStretch(EStretch::ScaleToFit);
    ViewportScaler->SetStretchDirection(EStretchDirection::Both);
    WidgetTree->RootWidget = ViewportScaler;

    USizeBox* DesignSurface = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("DesignSurface"));
    DesignSurface->SetWidthOverride(1920.0f);
    DesignSurface->SetHeightOverride(1080.0f);
    ViewportScaler->AddChild(DesignSurface);

    RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("RootCanvas"));
    DesignSurface->AddChild(RootCanvas);

    // The survival HUD is projected onto the inside of the pressure-suit visor. These soft,
    // translucent edge bands imply the helmet aperture without obscuring the player's view.
    auto AddVisorEdge = [&](const TCHAR* Name, const FVector2D& Position, const FVector2D& Size,
        const FLinearColor& Color)
    {
        UBorder* Edge = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), Name);
        Edge->SetBrushColor(Color);
        Edge->SetVisibility(ESlateVisibility::HitTestInvisible);
        AnchorTopLeft(RootCanvas, Edge, Position, Size);
    };
    const FLinearColor VisorShade(0.002f, 0.012f, 0.018f, 0.72f);
    const FLinearColor VisorRim(0.08f, 0.48f, 0.58f, 0.30f);
    AddVisorEdge(TEXT("VisorShadeTop"), FVector2D(0.0f, 0.0f), FVector2D(1920.0f, 30.0f), VisorShade);
    AddVisorEdge(TEXT("VisorShadeBottom"), FVector2D(0.0f, 1050.0f), FVector2D(1920.0f, 30.0f), VisorShade);
    AddVisorEdge(TEXT("VisorShadeLeft"), FVector2D(0.0f, 0.0f), FVector2D(24.0f, 1080.0f), VisorShade);
    AddVisorEdge(TEXT("VisorShadeRight"), FVector2D(1896.0f, 0.0f), FVector2D(24.0f, 1080.0f), VisorShade);
    AddVisorEdge(TEXT("VisorRimTop"), FVector2D(180.0f, 30.0f), FVector2D(1560.0f, 2.0f), VisorRim);
    AddVisorEdge(TEXT("VisorRimBottom"), FVector2D(180.0f, 1048.0f), FVector2D(1560.0f, 2.0f), VisorRim);
    AddVisorEdge(TEXT("VisorRimLeft"), FVector2D(24.0f, 170.0f), FVector2D(2.0f, 740.0f), VisorRim);
    AddVisorEdge(TEXT("VisorRimRight"), FVector2D(1894.0f, 170.0f), FVector2D(2.0f, 740.0f), VisorRim);

    // Four compact glass panels mirror the concept art and leave the central play space clear.
    AddHudPanel(WidgetTree, RootCanvas, TEXT("SuitPanel"), FVector2D(54.0f, 142.0f), FVector2D(344.0f, 210.0f));
    AddHudPanel(WidgetTree, RootCanvas, TEXT("LifeSupportPanel"), FVector2D(54.0f, 714.0f), FVector2D(344.0f, 246.0f));
    AddHudPanel(WidgetTree, RootCanvas, TEXT("NavigationPanel"), FVector2D(1432.0f, 88.0f), FVector2D(432.0f, 200.0f));
    AddHudPanel(WidgetTree, RootCanvas, TEXT("EquipmentPanel"), FVector2D(1492.0f, 720.0f), FVector2D(372.0f, 240.0f));

    VisorStatusText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("VisorStatusText"));
    VisorStatusText->SetText(FText::FromString(TEXT("VISOR LINK  //  PRESSURIZED")));
    VisorStatusText->SetColorAndOpacity(FSlateColor(HudCyanDim));
    VisorStatusText->SetJustification(ETextJustify::Center);
    AnchorTopLeft(RootCanvas, VisorStatusText, FVector2D(710.0f, 16.0f), FVector2D(500.0f, 22.0f));

    VisorReticleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("VisorReticleText"));
    VisorReticleText->SetText(FText::FromString(TEXT("(     o     )")));
    VisorReticleText->SetColorAndOpacity(FSlateColor(FLinearColor(0.25f, 0.92f, 1.0f, 0.58f)));
    VisorReticleText->SetJustification(ETextJustify::Center);
    AnchorTopLeft(RootCanvas, VisorReticleText, FVector2D(885.0f, 520.0f), FVector2D(150.0f, 24.0f));

    PsychosisGhostReticleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("PsychosisGhostReticleText"));
    PsychosisGhostReticleText->SetText(FText::FromString(TEXT("(     o     )")));
    PsychosisGhostReticleText->SetColorAndOpacity(FSlateColor(FLinearColor(0.85f, 0.12f, 0.26f, 0.0f)));
    PsychosisGhostReticleText->SetJustification(ETextJustify::Center);
    PsychosisGhostReticleText->SetVisibility(ESlateVisibility::Collapsed);
    AnchorTopLeft(RootCanvas, PsychosisGhostReticleText, FVector2D(891.0f, 518.0f), FVector2D(150.0f, 24.0f));

    auto AddPsychosisVoice = [&](const TCHAR* Name, const FVector2D& Position, TObjectPtr<UTextBlock>& OutText)
    {
        OutText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
        OutText->SetColorAndOpacity(FSlateColor(FLinearColor(0.9f, 0.35f, 0.48f, 0.9f)));
        OutText->SetJustification(ETextJustify::Center);
        OutText->SetVisibility(ESlateVisibility::Collapsed);
        AnchorTopLeft(RootCanvas, OutText, Position, FVector2D(440.0f, 34.0f));
    };
    AddPsychosisVoice(TEXT("PsychosisVoiceLeft"), FVector2D(80.0f, 430.0f), PsychosisVoiceLeftText);
    AddPsychosisVoice(TEXT("PsychosisVoiceCenter"), FVector2D(740.0f, 760.0f), PsychosisVoiceCenterText);
    AddPsychosisVoice(TEXT("PsychosisVoiceRight"), FVector2D(1400.0f, 430.0f), PsychosisVoiceRightText);

    DemoTitleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("DemoTitleText"));
    DemoTitleText->SetText(FText::FromString(TEXT("SUIT // CREW TELEMETRY")));
    DemoTitleText->SetColorAndOpacity(FSlateColor(HudCyan));
    AnchorTopLeft(RootCanvas, DemoTitleText, FVector2D(70.0f, 154.0f), FVector2D(300.0f, 24.0f));

    // The keys, for the first half minute on deck: the ship is played by people who have not read
    // the ini. It fades on its own.
    ControlsHintText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ControlsHintText"));
    ControlsHintText->SetText(FText::FromString(TEXT("E  INTERACT   //   F  CYCLE APPROACH   //   TAB  VIEW   //   ENTER  RESTART")));
    ControlsHintText->SetColorAndOpacity(FSlateColor(FLinearColor(HudCyan.R, HudCyan.G, HudCyan.B, 0.85f)));
    ControlsHintText->SetJustification(ETextJustify::Center);
    AnchorTopLeft(RootCanvas, ControlsHintText, FVector2D(560.0f, 1000.0f), FVector2D(800.0f, 26.0f));

    auto AddStatLabel = [&](const TCHAR* Name, const TCHAR* Label, float Y, TObjectPtr<UTextBlock>& OutLabel)
    {
        OutLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
        OutLabel->SetText(FText::FromString(Label));
        OutLabel->SetColorAndOpacity(FSlateColor(HudCyan));
        AnchorTopLeft(RootCanvas, OutLabel, FVector2D(70.0f, Y), FVector2D(90.0f, 18.0f));
    };

    auto AddValue = [&](const TCHAR* Name, float Y, TObjectPtr<UTextBlock>& OutValue)
    {
        OutValue = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
        OutValue->SetColorAndOpacity(FSlateColor(HudCyan));
        OutValue->SetJustification(ETextJustify::Right);
        AnchorTopLeft(RootCanvas, OutValue, FVector2D(326.0f, Y - 2.0f), FVector2D(54.0f, 20.0f));
    };

    HealthBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("HealthBar"));
    HealthBar->SetFillColorAndOpacity(HudCyan);
    AddStatLabel(TEXT("HealthLabel"), TEXT("VITAL"), 190.0f, HealthLabel);
    AnchorTopLeft(RootCanvas, HealthBar, FVector2D(158.0f, 190.0f), FVector2D(160.0f, 12.0f));
    AddValue(TEXT("HealthValue"), 190.0f, HealthValueText);

    OxygenBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("OxygenBar"));
    OxygenBar->SetFillColorAndOpacity(FLinearColor(0.2f, 0.6f, 1.0f));
    AddStatLabel(TEXT("OxygenLabel"), TEXT("O2"), 746.0f, OxygenLabel);
    AnchorTopLeft(RootCanvas, OxygenBar, FVector2D(158.0f, 746.0f), FVector2D(160.0f, 12.0f));
    AddValue(TEXT("OxygenValue"), 746.0f, OxygenValueText);

    SuitIntegrityBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("SuitIntegrityBar"));
    SuitIntegrityBar->SetFillColorAndOpacity(HudCyan);
    AddStatLabel(TEXT("SuitLabel"), TEXT("SEAL"), 226.0f, SuitLabel);
    AnchorTopLeft(RootCanvas, SuitIntegrityBar, FVector2D(158.0f, 226.0f), FVector2D(160.0f, 12.0f));
    AddValue(TEXT("SuitValue"), 226.0f, SuitValueText);

    StabilityBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("StabilityBar"));
    StabilityBar->SetFillColorAndOpacity(HudCyan);
    AddStatLabel(TEXT("StabilityLabel"), TEXT("STABLE"), 262.0f, StabilityLabel);
    AnchorTopLeft(RootCanvas, StabilityBar, FVector2D(158.0f, 262.0f), FVector2D(160.0f, 12.0f));
    AddValue(TEXT("StabilityValue"), 262.0f, StabilityValueText);

    ArmorBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("ArmorBar"));
    ArmorBar->SetFillColorAndOpacity(HudCyan);
    AddStatLabel(TEXT("ArmorLabel"), TEXT("ARMOR"), 298.0f, ArmorLabel);
    AnchorTopLeft(RootCanvas, ArmorBar, FVector2D(158.0f, 298.0f), FVector2D(160.0f, 12.0f));
    AddValue(TEXT("ArmorValue"), 298.0f, ArmorValueText);

    RadiationText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("RadiationText"));
    RadiationText->SetColorAndOpacity(FSlateColor(HudCyan));
    AnchorTopLeft(RootCanvas, RadiationText, FVector2D(70.0f, 790.0f), FVector2D(280.0f, 20.0f));

    ContaminationText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ContaminationText"));
    ContaminationText->SetColorAndOpacity(FSlateColor(HudAmber));
    AnchorTopLeft(RootCanvas, ContaminationText, FVector2D(70.0f, 824.0f), FVector2D(290.0f, 20.0f));

    StatusEffectsText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("StatusEffectsText"));
    StatusEffectsText->SetText(FText::FromString(TEXT("STATUS  //  NOMINAL")));
    StatusEffectsText->SetColorAndOpacity(FSlateColor(HudCyan));
    AnchorTopLeft(RootCanvas, StatusEffectsText, FVector2D(70.0f, 858.0f), FVector2D(310.0f, 88.0f));

    MagneticSuitText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("MagneticSuitText"));
    MagneticSuitText->SetColorAndOpacity(FSlateColor(HudCyan));
    AnchorTopLeft(RootCanvas, MagneticSuitText, FVector2D(1512.0f, 764.0f), FVector2D(330.0f, 42.0f));

    ThrusterFuelBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("ThrusterFuelBar"));
    ThrusterFuelBar->SetFillColorAndOpacity(HudCyan);
    AnchorTopLeft(RootCanvas, ThrusterFuelBar, FVector2D(1600.0f, 826.0f), FVector2D(170.0f, 12.0f));
    ThrusterValueText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ThrusterValueText"));
    ThrusterValueText->SetColorAndOpacity(FSlateColor(HudCyan));
    AnchorTopLeft(RootCanvas, ThrusterValueText, FVector2D(1512.0f, 820.0f), FVector2D(82.0f, 20.0f));

    ObjectiveText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ObjectiveText"));
    ObjectiveText->SetText(FText::FromString(TEXT("MISSION INITIALIZING...")));
    ObjectiveText->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.78f, 0.22f)));
    // Wrapped inside the visor's navigation panel: an objective title with a range and a sentence
    // of description ran off the right edge of the frame unwrapped.
    ObjectiveText->SetAutoWrapText(true);
    AnchorTopLeft(RootCanvas, ObjectiveText, FVector2D(1450.0f, 154.0f), FVector2D(396.0f, 120.0f));

    CompassText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("CompassText"));
    CompassText->SetText(FText::FromString(TEXT("W      NW       N       NE      E")));
    CompassText->SetColorAndOpacity(FSlateColor(HudCyan));
    CompassText->SetJustification(ETextJustify::Center);
    AnchorTopLeft(RootCanvas, CompassText, FVector2D(1450.0f, 108.0f), FVector2D(390.0f, 22.0f));

    ControlsText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ControlsText"));
    ControlsText->SetText(FText::FromString(TEXT("WASD MOVE // MOUSE LOOK // E INTERACT // M BOOTS // SHIFT GRIP // R ROTATE // Q THROW // SPACE PUSH OFF // ENTER RESTART")));
    ControlsText->SetColorAndOpacity(FSlateColor(FLinearColor(0.55f, 0.62f, 0.66f)));
    ControlsText->SetVisibility(ESlateVisibility::Collapsed);

    InteractionPromptPanel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("InteractionPromptPanel"));
    InteractionPromptPanel->SetBrushColor(FLinearColor(0.005f, 0.03f, 0.04f, 0.88f));
    InteractionPromptPanel->SetVisibility(ESlateVisibility::Collapsed);
    AnchorTopLeft(RootCanvas, InteractionPromptPanel, FVector2D(700.0f, 638.0f), FVector2D(520.0f, 52.0f));

    InteractionPromptText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InteractionPromptText"));
    InteractionPromptText->SetColorAndOpacity(FSlateColor(FLinearColor(0.35f, 1.0f, 0.55f)));
    InteractionPromptText->SetJustification(ETextJustify::Center);
    AnchorTopLeft(RootCanvas, InteractionPromptText, FVector2D(760.0f, 650.0f), FVector2D(400.0f, 30.0f));

    JumpWarningText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("JumpWarningText"));
    JumpWarningText->SetColorAndOpacity(FSlateColor(HudAmber));
    JumpWarningText->SetJustification(ETextJustify::Center);
    JumpWarningText->SetVisibility(ESlateVisibility::Collapsed);
    AnchorTopLeft(RootCanvas, JumpWarningText, FVector2D(660.0f, 72.0f), FVector2D(600.0f, 30.0f));

    LifeSupportWarningText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("LifeSupportWarningText"));
    LifeSupportWarningText->SetText(FText::FromString(TEXT("LIFE SUPPORT CRITICAL")));
    LifeSupportWarningText->SetColorAndOpacity(FSlateColor(FLinearColor::Red));
    LifeSupportWarningText->SetJustification(ETextJustify::Center);
    LifeSupportWarningText->SetVisibility(ESlateVisibility::Collapsed);
    AnchorTopLeft(RootCanvas, LifeSupportWarningText, FVector2D(660.0f, 106.0f), FVector2D(600.0f, 30.0f));

    DeathText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("DeathText"));
    DeathText->SetColorAndOpacity(FSlateColor(FLinearColor::White));
    DeathText->SetJustification(ETextJustify::Center);
    DeathText->SetVisibility(ESlateVisibility::Collapsed);
    AnchorTopLeft(RootCanvas, DeathText, FVector2D(560.0f, 470.0f), FVector2D(800.0f, 42.0f));

    SelfDestructWarningText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SelfDestructWarningText"));
    SelfDestructWarningText->SetColorAndOpacity(FSlateColor(FLinearColor::Red));
    SelfDestructWarningText->SetJustification(ETextJustify::Center);
    SelfDestructWarningText->SetVisibility(ESlateVisibility::Collapsed);
    AnchorTopLeft(RootCanvas, SelfDestructWarningText, FVector2D(660.0f, 140.0f), FVector2D(600.0f, 30.0f));

    AlertLineText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("AlertLineText"));
    AlertLineText->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.34f, 0.18f)));
    AlertLineText->SetJustification(ETextJustify::Center);
    AlertLineText->SetVisibility(ESlateVisibility::Collapsed);
    AnchorTopLeft(RootCanvas, AlertLineText, FVector2D(560.0f, 174.0f), FVector2D(800.0f, 30.0f));

    RunOutcomePanel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("RunOutcomePanel"));
    RunOutcomePanel->SetBrushColor(FLinearColor(0.004f, 0.014f, 0.02f, 0.96f));
    RunOutcomePanel->SetVisibility(ESlateVisibility::Collapsed);
    AnchorTopLeft(RootCanvas, RunOutcomePanel, FVector2D(570.0f, 350.0f), FVector2D(780.0f, 330.0f));

    RunOutcomeText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("RunOutcomeText"));
    RunOutcomeText->SetColorAndOpacity(FSlateColor(HudCyan));
    RunOutcomeText->SetJustification(ETextJustify::Center);
    RunOutcomeText->SetVisibility(ESlateVisibility::Collapsed);
    AnchorTopLeft(RootCanvas, RunOutcomeText, FVector2D(620.0f, 420.0f), FVector2D(680.0f, 190.0f));

    CharacterNameText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("CharacterNameText"));
    CharacterNameText->SetColorAndOpacity(FSlateColor(FLinearColor::White));
    CharacterNameText->SetColorAndOpacity(FSlateColor(HudCyanDim));
    CharacterNameText->SetJustification(ETextJustify::Right);
    AnchorTopLeft(RootCanvas, CharacterNameText, FVector2D(1540.0f, 32.0f), FVector2D(300.0f, 24.0f));

    NavigationContactText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("NavigationContactText"));
    NavigationContactText->SetColorAndOpacity(FSlateColor(FLinearColor(0.3f, 1.0f, 0.55f)));
    NavigationContactText->SetJustification(ETextJustify::Center);
    NavigationContactText->SetVisibility(ESlateVisibility::Collapsed);
    AnchorTopLeft(RootCanvas, NavigationContactText, FVector2D(650.0f, 58.0f), FVector2D(620.0f, 54.0f));

    ActivityMinigameWidget = WidgetTree->ConstructWidget<UActivityMinigameWidget>(UActivityMinigameWidget::StaticClass(), TEXT("ActivityMinigame"));
    ActivityMinigameWidget->SetVisibility(ESlateVisibility::Collapsed);
    AnchorTopLeft(RootCanvas, ActivityMinigameWidget, FVector2D(460.0f, 150.0f), FVector2D(1000.0f, 650.0f));

    // Bottom-centre, above the status bars: an ability you have to look away from the world to
    // read is one you will not use in the moment you brought it for.
    AbilityBarWidget = WidgetTree->ConstructWidget<USkillAbilityBarWidget>(USkillAbilityBarWidget::StaticClass(), TEXT("AbilityBar"));
    AnchorTopLeft(RootCanvas, AbilityBarWidget, FVector2D(760.0f, 880.0f), FVector2D(420.0f, 92.0f));
}

void USurvivalHUDWidget::NativeDestruct()
{
    if (OwningCharacter)
    {
        if (UPlayerPsychosisComponent* Psychosis = OwningCharacter->GetPsychosisComponent())
        {
            Psychosis->OnPsychosisVoice.RemoveDynamic(this, &USurvivalHUDWidget::OnPsychosisVoiceReceived);
        }
    }
    if (UGameInstance* GI = GetGameInstance())
    {
        if (UCharacterProfileSubsystem* ProfileSubsystem = GI->GetSubsystem<UCharacterProfileSubsystem>())
        {
            ProfileSubsystem->OnCharacterProfileChanged.RemoveDynamic(this, &USurvivalHUDWidget::OnCharacterProfileChanged);
        }
    }

    Super::NativeDestruct();
}

void USurvivalHUDWidget::ShowAlertLine(const FText& Line, float Seconds)
{
    AlertLineSecondsRemaining = FMath::Max(0.1f, Seconds);
    if (AlertLineText)
    {
        AlertLineText->SetText(Line);
        AlertLineText->SetVisibility(ESlateVisibility::HitTestInvisible);
    }
}

void USurvivalHUDWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);

    AlertPulseTime += InDeltaTime;
    if (ControlsHintText)
    {
        const float Fade = FMath::Clamp((ControlsHintSeconds - AlertPulseTime) / 4.0f, 0.0f, 1.0f);
        ControlsHintText->SetVisibility(Fade > 0.0f ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
        ControlsHintText->SetRenderOpacity(Fade);
    }
    PsychosisVoiceSecondsRemaining = FMath::Max(0.0f, PsychosisVoiceSecondsRemaining - InDeltaTime);
    if (PsychosisVoiceSecondsRemaining <= 0.0f)
    {
        if (PsychosisVoiceLeftText) PsychosisVoiceLeftText->SetVisibility(ESlateVisibility::Collapsed);
        if (PsychosisVoiceCenterText) PsychosisVoiceCenterText->SetVisibility(ESlateVisibility::Collapsed);
        if (PsychosisVoiceRightText) PsychosisVoiceRightText->SetVisibility(ESlateVisibility::Collapsed);
    }
    const float AlertOpacity = 0.58f + (0.42f * (0.5f + 0.5f * FMath::Sin(AlertPulseTime * 7.0f)));
    auto PulseAlert = [AlertOpacity](UTextBlock* Alert)
    {
        if (Alert && Alert->GetVisibility() != ESlateVisibility::Collapsed)
        {
            Alert->SetRenderOpacity(AlertOpacity);
        }
    };
    PulseAlert(JumpWarningText);
    PulseAlert(LifeSupportWarningText);
    PulseAlert(SelfDestructWarningText);

    if (AlertLineSecondsRemaining > 0.0f)
    {
        AlertLineSecondsRemaining = FMath::Max(0.0f, AlertLineSecondsRemaining - InDeltaTime);
        if (AlertLineSecondsRemaining <= 0.0f && AlertLineText)
        {
            AlertLineText->SetVisibility(ESlateVisibility::Collapsed);
        }
        else
        {
            PulseAlert(AlertLineText);
        }
    }

    TimeSinceLastUpdate += InDeltaTime;
    if (TimeSinceLastUpdate >= UpdateInterval)
    {
        TimeSinceLastUpdate = 0.0f;
        RefreshAllStats();
    }
}

void USurvivalHUDWidget::SetCharacterReference(ACoopSurvivalCharacter* InCharacter)
{
    if (OwningCharacter)
    {
        if (UPlayerPsychosisComponent* OldPsychosis = OwningCharacter->GetPsychosisComponent())
        {
            OldPsychosis->OnPsychosisVoice.RemoveDynamic(this, &USurvivalHUDWidget::OnPsychosisVoiceReceived);
        }
    }
    OwningCharacter = InCharacter;
    if (AbilityBarWidget)
    {
        AbilityBarWidget->SetCharacterReference(InCharacter);
    }
    if (OwningCharacter)
    {
        if (UPlayerPsychosisComponent* Psychosis = OwningCharacter->GetPsychosisComponent())
        {
            Psychosis->OnPsychosisVoice.AddUniqueDynamic(this, &USurvivalHUDWidget::OnPsychosisVoiceReceived);
        }
    }
}

void USurvivalHUDWidget::OnPsychosisVoiceReceived(EPsychosisVoiceIntent Intent, const FText& Line,
    FVector PerceivedLocation, float Severity)
{
    if (!OwningCharacter) return;
    UTextBlock* Target = PsychosisVoiceCenterText;
    const FVector ToVoice = (PerceivedLocation - OwningCharacter->GetActorLocation()).GetSafeNormal();
    const float Side = FVector::DotProduct(ToVoice, OwningCharacter->GetActorRightVector());
    if (Side < -0.25f) Target = PsychosisVoiceLeftText;
    else if (Side > 0.25f) Target = PsychosisVoiceRightText;
    if (!Target) return;

    if (PsychosisVoiceLeftText) PsychosisVoiceLeftText->SetVisibility(ESlateVisibility::Collapsed);
    if (PsychosisVoiceCenterText) PsychosisVoiceCenterText->SetVisibility(ESlateVisibility::Collapsed);
    if (PsychosisVoiceRightText) PsychosisVoiceRightText->SetVisibility(ESlateVisibility::Collapsed);
    Target->SetText(Line);
    const bool bGrounding = Intent == EPsychosisVoiceIntent::Grounding;
    Target->SetColorAndOpacity(FSlateColor(bGrounding ? FLinearColor(0.2f, 0.9f, 1.0f, 0.92f)
        : FLinearColor(1.0f, 0.18f, 0.35f, FMath::Lerp(0.65f, 1.0f, Severity))));
    Target->SetVisibility(ESlateVisibility::HitTestInvisible);
    PsychosisVoiceSecondsRemaining = FMath::Lerp(1.5f, 4.0f, Severity);
}

void USurvivalHUDWidget::UpdateDisplay()
{
    RefreshAllStats();
}

void USurvivalHUDWidget::SetHealth_Implementation(float HealthPercent)
{
    HealthPercent = FMath::Clamp(HealthPercent, 0.0f, 100.0f);
    if (HealthBar)
    {
        HealthBar->SetPercent(HealthPercent / 100.0f);
        HealthBar->SetFillColorAndOpacity(HealthPercent <= 25.0f ? HudAmber : HudCyan);
    }
    if (HealthValueText)
    {
        HealthValueText->SetText(FText::FromString(FString::Printf(TEXT("%03.0f%%"), HealthPercent)));
    }
}

void USurvivalHUDWidget::SetOxygen_Implementation(float OxygenLevelPercent)
{
    OxygenLevelPercent = FMath::Clamp(OxygenLevelPercent, 0.0f, 100.0f);
    if (OxygenBar)
    {
        OxygenBar->SetPercent(OxygenLevelPercent / 100.0f);
        OxygenBar->SetFillColorAndOpacity(OxygenLevelPercent <= 25.0f ? HudAmber : HudCyan);
    }
    if (OxygenValueText)
    {
        OxygenValueText->SetText(FText::FromString(FString::Printf(TEXT("%03.0f%%"), OxygenLevelPercent)));
    }
}

void USurvivalHUDWidget::SetRadiation_Implementation(float RadiationSv)
{
    if (RadiationText)
    {
        RadiationSv = FMath::Max(0.0f, RadiationSv);
        RadiationText->SetText(FText::FromString(FString::Printf(TEXT("RAD     %05.2f Sv"), RadiationSv)));
        RadiationText->SetColorAndOpacity(FSlateColor(RadiationSv >= 1.0f ? FLinearColor::Red : (RadiationSv >= 0.25f ? HudAmber : HudCyan)));
    }
}

void USurvivalHUDWidget::SetSuitIntegrity_Implementation(float SuitIntegrityPercent)
{
    SuitIntegrityPercent = FMath::Clamp(SuitIntegrityPercent, 0.0f, 100.0f);
    if (SuitIntegrityBar)
    {
        SuitIntegrityBar->SetPercent(SuitIntegrityPercent / 100.0f);
        SuitIntegrityBar->SetFillColorAndOpacity(SuitIntegrityPercent <= 30.0f ? HudAmber : HudCyan);
    }
    if (SuitValueText)
    {
        SuitValueText->SetText(FText::FromString(FString::Printf(TEXT("%03.0f%%"), SuitIntegrityPercent)));
    }
}

void USurvivalHUDWidget::SetStability_Implementation(float StabilityPercent)
{
    StabilityPercent = FMath::Clamp(StabilityPercent, 0.0f, 100.0f);
    if (StabilityBar)
    {
        StabilityBar->SetPercent(StabilityPercent / 100.0f);
        StabilityBar->SetFillColorAndOpacity(StabilityPercent <= 30.0f ? HudAmber : HudCyan);
    }
    if (StabilityValueText)
    {
        StabilityValueText->SetText(FText::FromString(FString::Printf(TEXT("%03.0f%%"), StabilityPercent)));
    }
}

void USurvivalHUDWidget::SetArmorStatus_Implementation(float ArmorIntegrity, bool bIsCorrupted)
{
    if (ArmorBar)
    {
        const float ArmorPercent = FMath::Clamp(ArmorIntegrity, 0.0f, 1.0f);
        ArmorBar->SetPercent(ArmorPercent);
        if (bIsCorrupted)
        {
            ArmorBar->SetFillColorAndOpacity(HudAmber);
        }
        else
        {
            ArmorBar->SetFillColorAndOpacity(HudCyan);
        }
        if (ArmorValueText)
        {
            ArmorValueText->SetText(FText::FromString(FString::Printf(TEXT("%03.0f%%"), ArmorPercent * 100.0f)));
            ArmorValueText->SetColorAndOpacity(FSlateColor(bIsCorrupted ? HudAmber : HudCyan));
        }
    }
}

void USurvivalHUDWidget::OnPlayerDeath_Implementation(float RespawnCountdown)
{
    if (DeathText)
    {
        DeathText->SetVisibility(ESlateVisibility::Visible);
        DeathText->SetText(FText::FromString(FString::Printf(TEXT("VITAL LINK LOST  //  RECLONING IN %.0fs"), FMath::Max(0.0f, RespawnCountdown))));
    }
}

void USurvivalHUDWidget::OnPlayerRespawn_Implementation()
{
    if (DeathText)
    {
        DeathText->SetVisibility(ESlateVisibility::Collapsed);
    }
}

void USurvivalHUDWidget::SetContaminationReading_Implementation(float Concentration)
{
    if (ContaminationText)
    {
        ContaminationText->SetText(FText::FromString(FString::Printf(TEXT("BLOOM   %s  %05.2f"),
            Concentration >= 0.65f ? TEXT("HIGH") : (Concentration >= 0.25f ? TEXT("WATCH") : TEXT("LOW")), Concentration)));
        ContaminationText->SetColorAndOpacity(FSlateColor(Concentration >= 0.25f ? HudAmber : HudCyan));
    }
}

void USurvivalHUDWidget::SetInteractionPrompt_Implementation(const FString& Prompt)
{
    const ESlateVisibility PromptVisibility = Prompt.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible;
    if (InteractionPromptPanel)
    {
        InteractionPromptPanel->SetVisibility(PromptVisibility);
    }
    if (InteractionPromptText)
    {
        InteractionPromptText->SetText(FText::FromString(Prompt));
        InteractionPromptText->SetVisibility(PromptVisibility);
    }
}

void USurvivalHUDWidget::SetJumpWarning_Implementation(bool bActive, float SecondsRemaining)
{
    if (JumpWarningText)
    {
        JumpWarningText->SetVisibility(bActive ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        if (bActive)
        {
            JumpWarningText->SetText(FText::FromString(FString::Printf(TEXT("FTL ENVELOPE  //  JUMP IN %.0fs"), FMath::Max(0.0f, SecondsRemaining))));
        }
    }
}

void USurvivalHUDWidget::SetLifeSupportCritical_Implementation(bool bCritical)
{
    if (LifeSupportWarningText)
    {
        LifeSupportWarningText->SetVisibility(bCritical ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    }
}

void USurvivalHUDWidget::SetSelfDestructWarning_Implementation(bool bActive, float SecondsRemaining)
{
    if (SelfDestructWarningText)
    {
        SelfDestructWarningText->SetVisibility(bActive ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        if (bActive)
        {
            SelfDestructWarningText->SetText(FText::FromString(FString::Printf(TEXT("REACTOR SCUTTLE ARMED  //  %.0fs"), FMath::Max(0.0f, SecondsRemaining))));
        }
    }
}

void USurvivalHUDWidget::ShowRunOutcome_Implementation(uint8 Outcome, int32 CurrencyEarned, int32 TotalBankedCurrency)
{
    if (!RunOutcomeText)
    {
        return;
    }

    static const TCHAR* OutcomeLabels[] =
    {
        TEXT("In Progress"),
        TEXT("VICTORY"),
        TEXT("BLOOM REACHED THE DESTINATION"),
        TEXT("SELF-DESTRUCT SUCCESSFUL"),
        TEXT("SELF-DESTRUCT COUNTERED")
    };

    const TCHAR* Label = Outcome < UE_ARRAY_COUNT(OutcomeLabels) ? OutcomeLabels[Outcome] : TEXT("Unknown");

    RunOutcomeText->SetVisibility(ESlateVisibility::Visible);
    if (RunOutcomePanel) RunOutcomePanel->SetVisibility(ESlateVisibility::HitTestInvisible);
    RunOutcomeText->SetText(FText::FromString(FString::Printf(TEXT("EXPEDITION CLOSED  //  %s\nSALVAGE RECOVERED  %d\nBANKED SALVAGE     %d"),
        Label, FMath::Max(0, CurrencyEarned), FMath::Max(0, TotalBankedCurrency))));
}

void USurvivalHUDWidget::RefreshInteractionPrompt()
{
	// The prompt panel has existed since this widget was written and nothing has ever filled it.
	// Every interactable in the ship has been silent, so the only way to learn that a thing can be
	// used has been to walk into it and press the key.
	if (!OwningCharacter)
	{
		SetInteractionPrompt(FString());
		return;
	}

	const UInteractionComponent* Interaction =
		OwningCharacter->FindComponentByClass<UInteractionComponent>();
	AActor* Focused = Interaction ? Interaction->GetFocusedInteractable() : nullptr;

	if (!Focused || !Focused->Implements<UInteractable>())
	{
		SetInteractionPrompt(FString());
		return;
	}

	// Asked of the object rather than assembled here, because what a thing offers is a property of
	// the thing. An obstruction lists the ways past it; a station names its work; a station that
	// cannot be used says why.
	const FText Prompt = IInteractable::Execute_GetInteractionPrompt(
		Focused, Cast<APawn>(OwningCharacter));

	SetInteractionPrompt(Prompt.IsEmpty() ? FString() : Prompt.ToString());
}

void USurvivalHUDWidget::RefreshAllStats()
{
	RefreshInteractionPrompt();

    if (!OwningCharacter)
    {
        return;
    }

    SetHealth(OwningCharacter->HealthPercent);
    SetOxygen(OwningCharacter->OxygenLevelPercent);
    SetRadiation(OwningCharacter->RadiationDoseSv);
    SetSuitIntegrity(OwningCharacter->SuitIntegrity * 100.0f);
    SetStability(OwningCharacter->Stability * 100.0f);

    if (StatusEffectsText)
    {
        FString StatusSummary;
        if (const UPlayerStatusEffectComponent* StatusEffects = OwningCharacter->GetStatusEffectComponent())
        {
            TArray<FPlayerStatusEffectState> ActiveEffects = StatusEffects->GetActiveStatusEffects();
            ActiveEffects.Sort([](const FPlayerStatusEffectState& A, const FPlayerStatusEffectState& B)
            {
                return A.Severity > B.Severity;
            });
            for (const FPlayerStatusEffectState& Effect : ActiveEffects)
            {
                const int32 Percent = FMath::RoundToInt(Effect.Severity * 100.0f);
                const TCHAR* CriticalMarker = StatusEffects->GetClinicalSeverity(Effect.Type) == EPlayerStatusSeverity::Critical
                    ? TEXT("! ") : TEXT("");
                StatusSummary += FString::Printf(TEXT("%s%s  %d%%\n"), CriticalMarker,
                    *UPlayerStatusEffectComponent::GetStatusDisplayName(Effect.Type).ToString().ToUpper(), Percent);
            }
        }
        StatusEffectsText->SetText(FText::FromString(StatusSummary.IsEmpty() ? TEXT("STATUS  //  NOMINAL") : StatusSummary));
        StatusEffectsText->SetColorAndOpacity(FSlateColor(StatusSummary.IsEmpty() ? HudCyan : HudAmber));
    }
    if (PsychosisGhostReticleText)
    {
        const UPlayerPsychosisComponent* Psychosis = OwningCharacter->GetPsychosisComponent();
        const float PsychosisSeverity = Psychosis ? Psychosis->GetEffectiveSeverity() : 0.0f;
        const bool bShowDistortion = PsychosisSeverity >= 0.3f;
        PsychosisGhostReticleText->SetVisibility(bShowDistortion ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
        PsychosisGhostReticleText->SetColorAndOpacity(FSlateColor(FLinearColor(0.95f, 0.08f, 0.25f,
            FMath::Clamp((PsychosisSeverity - 0.25f) * 0.55f, 0.0f, 0.38f))));
        const float Jitter = FMath::Sin(AlertPulseTime * FMath::Lerp(3.0f, 13.0f, PsychosisSeverity)) * PsychosisSeverity * 8.0f;
        PsychosisGhostReticleText->SetRenderTranslation(FVector2D(Jitter, -Jitter * 0.35f));
    }

    if (MagneticSuitText)
    {
        const TCHAR* Target = OwningCharacter->HasValidMagneticTarget() ? TEXT("TARGET: METAL") : TEXT("TARGET: ---");
        // Under drive the deck has gravity and the boots are moot: say so, rather than "MAG BOOTS
        // OFF" on a ship you are plainly standing in.
        const UShipPropulsionSubsystem* Propulsion = OwningCharacter->GetWorld() ? OwningCharacter->GetWorld()->GetSubsystem<UShipPropulsionSubsystem>() : nullptr;
        FString Footing;
        if (Propulsion && Propulsion->IsShipThrusting())
        {
            // The zero-g component turns acceleration into gravity at 0.0001 g per cm/s^2, so one g is 10,000.
            Footing = FString::Printf(TEXT("DRIVE GRAVITY %.1fg"), Propulsion->GetPseudoGravity().Size() * 0.0001f);
        }
        else
        {
            Footing = FString::Printf(TEXT("MAG  BOOTS %s"), OwningCharacter->AreMagneticBootsEnabled() ? TEXT("ON") : TEXT("OFF"));
        }
        MagneticSuitText->SetText(FText::FromString(FString::Printf(TEXT("%s\nGRIP L %s  R %s  //  %s"), *Footing,
            OwningCharacter->IsLeftMagneticGloveActive() ? TEXT("GRIP") : TEXT("---"),
            OwningCharacter->IsRightMagneticGloveActive() ? TEXT("GRIP") : TEXT("---"), Target)));
    }
    if (ThrusterFuelBar)
    {
        const float FuelPercent = OwningCharacter->GetThrusterFuelPercent();
        ThrusterFuelBar->SetPercent(FuelPercent / 100.0f);
        ThrusterFuelBar->SetFillColorAndOpacity(OwningCharacter->IsRotationThrusterActive() ?
            HudAmber : HudCyan);
        if (ThrusterValueText)
        {
            ThrusterValueText->SetText(FText::FromString(FString::Printf(TEXT("PWR %03.0f%%"), FuelPercent)));
        }
    }

    SetLifeSupportCritical(OwningCharacter->OxygenDrainMultiplier >= LifeSupportCriticalDrainMultiplierThreshold);

    if (UGameInstance* GI = OwningCharacter->GetGameInstance())
    {
        if (ObjectiveText)
        {
            if (UMissionObjectiveSubsystem* Missions = GI->GetSubsystem<UMissionObjectiveSubsystem>())
            {
                const TArray<FMissionObjectiveRuntime> ActiveObjectives = Missions->GetActiveObjectives();
                if (!ActiveObjectives.IsEmpty())
                {
                    const FMissionObjectiveRuntime& Objective = ActiveObjectives[0];
                    FString RangeText;
                    for (TActorIterator<AQuickDemoObjectiveBeacon> It(OwningCharacter->GetWorld()); It; ++It)
                    {
                        if (It->ObjectiveId == Objective.Definition.ObjectiveId)
                        {
                            const int32 DistanceMeters = FMath::Max(1,
                                FMath::RoundToInt(FVector::Dist(OwningCharacter->GetActorLocation(),
                                    It->GetActorLocation()) / 100.0f));
                            RangeText = FString::Printf(TEXT("  //  RANGE %dm"), DistanceMeters);
                            break;
                        }
                    }
                    ObjectiveText->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.78f, 0.22f)));
                    ObjectiveText->SetText(FText::FromString(FString::Printf(TEXT("OBJECTIVE  //  %s%s\n%s"),
                        *Objective.Definition.Title.ToString(), *RangeText,
                        *Objective.Definition.Description.ToString())));
                }
                else if (Missions->AreRequiredObjectivesResolved())
                {
                    ObjectiveText->SetColorAndOpacity(FSlateColor(FLinearColor(0.3f, 1.0f, 0.55f)));
                    const bool bQuickDemo = OwningCharacter->GetWorld()
                        && OwningCharacter->GetWorld()->GetMapName().Contains(TEXT("QuickDemo_FourDeck"));
                    ObjectiveText->SetText(FText::FromString(bQuickDemo
                        ? TEXT("SHIP STABILIZED  //  CIC ONLINE\nFour-deck prototype mission complete.")
                        : TEXT("DISTRICT SECURED  //  TRANSIT UNLOCKED\nProceed to the transit console to continue the demo.")));
                }
            }
        }

        if (UJumpSequenceSubsystem* JumpSequence = GI->GetSubsystem<UJumpSequenceSubsystem>())
        {
            SetJumpWarning(JumpSequence->CurrentPhase == EJumpPhase::WarningCountdown, JumpSequence->WarningSecondsRemaining);
        }

        if (URunOutcomeSubsystem* RunOutcome = GI->GetSubsystem<URunOutcomeSubsystem>())
        {
            SetSelfDestructWarning(RunOutcome->bSelfDestructArmed, RunOutcome->SelfDestructSecondsRemaining);

            if (RunOutcome->bRunResolved && !bHasShownRunOutcome)
            {
                bHasShownRunOutcome = true;
                ShowRunOutcome(static_cast<uint8>(RunOutcome->CurrentOutcome), RunOutcome->LastCurrencyEarned, RunOutcome->TotalBankedCurrency);
            }
        }
    }

    if (!CachedSensorArray)
    {
        for (TActorIterator<ASensorArraySystem> It(OwningCharacter->GetWorld()); It; ++It)
        {
            CachedSensorArray = *It;
            break;
        }
    }

    if (NavigationContactText)
    {
        const bool bHasTrackedContact = CachedSensorArray && CachedSensorArray->HasTrackedContact();
        NavigationContactText->SetVisibility(bHasTrackedContact ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        if (bHasTrackedContact)
        {
            const FSensorContact Contact = CachedSensorArray->GetTrackedContact();
            const TCHAR* SteeringCue = Contact.BearingDegrees < -5.0f ? TEXT("<<<") : (Contact.BearingDegrees > 5.0f ? TEXT(">>>") : TEXT("| ON COURSE |"));
            NavigationContactText->SetText(FText::FromString(FString::Printf(TEXT("%s  %s  %s\n%.1f km  //  BRG %+06.1f"),
                SteeringCue, *Contact.DisplayName.ToString(), SteeringCue, Contact.DistanceKilometers, Contact.BearingDegrees)));

            for (TActorIterator<AShipHelmSystem> It(OwningCharacter->GetWorld()); It; ++It)
            {
                const FHelmNavigationSolution Solution = It->CurrentNavigationSolution;
                if (Solution.bRouteIntersectsHazard)
                {
                    if (Solution.bUsingSafeDetour)
                    {
                        NavigationContactText->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.68f, 0.16f)));
                        NavigationContactText->SetText(FText::FromString(FString::Printf(
                            TEXT("SAFE DETOUR ACTIVE // %s // ETA %.0fs\n%s  %.1f km  //  BRG %+06.1f"),
                            *Solution.ClosestHazardName.ToString(), Solution.DetourTravelSeconds,
                            *Contact.DisplayName.ToString(), Contact.DistanceKilometers, Contact.BearingDegrees)));
                    }
                    else
                    {
                        NavigationContactText->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.22f, 0.08f)));
                        NavigationContactText->SetText(FText::FromString(FString::Printf(
                            TEXT("ROUTE HAZARD // %s // CLEARANCE %.1f km\n%s  %.1f km  //  BRG %+06.1f"),
                            *Solution.ClosestHazardName.ToString(), Solution.ClosestHazardClearanceKilometers,
                            *Contact.DisplayName.ToString(), Contact.DistanceKilometers, Contact.BearingDegrees)));
                    }
                }
                else
                {
                    NavigationContactText->SetColorAndOpacity(FSlateColor(FLinearColor(0.3f, 1.0f, 0.55f)));
                    if (Solution.bBraking)
                    {
                        NavigationContactText->SetColorAndOpacity(FSlateColor(FLinearColor(0.3f, 0.75f, 1.0f)));
                        NavigationContactText->SetText(FText::FromString(FString::Printf(
                            TEXT("ARRIVAL BURN // AUTOMATIC BRAKING\n%s  %.1f km  //  BRG %+06.1f"),
                            *Contact.DisplayName.ToString(), Contact.DistanceKilometers, Contact.BearingDegrees)));
                    }
                }
                break;
            }
        }
    }

    if (UBioScannerComponent* Scanner = OwningCharacter->GetBioScannerComponent())
    {
        SetContaminationReading(Scanner->LocalReading.Concentration);
    }
    if (const UPlayerPsychosisComponent* Psychosis = OwningCharacter->GetPsychosisComponent();
        Psychosis && Psychosis->IsFalseInfectionVisible())
    {
        // Fabricated local telemetry must use the exact same presentation path as a genuine
        // scanner reading. Any false-only copy, color, icon, or animation would reveal hidden
        // truth to the player and defeat the hallucination.
        SetContaminationReading(FMath::Max(0.7f, Psychosis->GetFalseInfectionSeverity()));
    }

    if (UPlayerActivityComponent* Activity = OwningCharacter->GetPlayerActivityComponent(); Activity && Activity->IsActivityActive())
    {
        const FPlayerActivitySnapshot& ActivityState = Activity->GetSnapshot();
        if (ActivityMinigameWidget) ActivityMinigameWidget->UpdateFromSnapshot(ActivityState);
        const bool bFullMinigame = ActivityMinigameWidget && ActivityMinigameWidget->IsShowingMinigame();
        if (VisorReticleText) VisorReticleText->SetVisibility(bFullMinigame ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
        if (PsychosisGhostReticleText && bFullMinigame) PsychosisGhostReticleText->SetVisibility(ESlateVisibility::Collapsed);
        const int32 Percent = FMath::RoundToInt(ActivityState.Progress * 100.0f);
        const FString BloomWarning = ActivityState.BloomInterference >= 0.2f
            ? FString::Printf(TEXT("  //  BLOOM NOISE %d%%"), FMath::RoundToInt(ActivityState.BloomInterference * 100.0f)) : FString();
        if (ActivityState.Mechanic == EActivityMechanic::ToolPath)
        {
            SetInteractionPrompt(FString::Printf(TEXT("%s  //  SEAM %d%%  //  ACCURACY %d%%%s  //  AIM TO CORRECT  //  [ X ] CANCEL"),
                *ActivityState.DisplayName.ToString().ToUpper(), Percent,
                FMath::RoundToInt(ActivityState.ToolAccuracy * 100.0f), *BloomWarning));
        }
        else if (bFullMinigame)
        {
            SetInteractionPrompt(TEXT(""));
        }
        else if (ActivityState.TotalInputs > 0)
        {
            const TCHAR* Expected = TEXT("E");
            switch (ActivityState.ExpectedInput)
            {
            case EActivityInput::Secondary: Expected = TEXT("F"); break;
            case EActivityInput::Tertiary: Expected = TEXT("3"); break;
            case EActivityInput::Quaternary: Expected = TEXT("4"); break;
            default: break;
            }
            const TCHAR* PuzzleLabel = TEXT("MATCH CABLE");
            if (ActivityState.Mechanic == EActivityMechanic::GenomeSequence) PuzzleLabel = TEXT("ALIGN BASE");
            else if (ActivityState.Mechanic == EActivityMechanic::OrderedAssembly) PuzzleLabel = TEXT("FIT PART");
            else if (ActivityState.Mechanic == EActivityMechanic::DiagnosticSequence) PuzzleLabel = TEXT("APPLY CARE");
            SetInteractionPrompt(FString::Printf(TEXT("%s  //  %s [ %s ]  //  %d/%d CONFIRMED  //  ERRORS %d%s  //  [ X ] CANCEL"),
                *ActivityState.DisplayName.ToString().ToUpper(), PuzzleLabel, Expected,
                ActivityState.CurrentInputIndex, ActivityState.TotalInputs, ActivityState.Mistakes, *BloomWarning));
        }
        else
        {
            SetInteractionPrompt(FString::Printf(TEXT("%s  //  %d%%  //  [ X ] CANCEL"),
                *ActivityState.DisplayName.ToString().ToUpper(), Percent));
        }
    }
    else if (UInteractionComponent* Interaction = OwningCharacter->GetInteractionComponent())
    {
        if (ActivityMinigameWidget) ActivityMinigameWidget->SetVisibility(ESlateVisibility::Collapsed);
        if (VisorReticleText) VisorReticleText->SetVisibility(ESlateVisibility::HitTestInvisible);
        FString Prompt;
        if (AActor* Focused = Interaction->GetFocusedInteractable())
        {
            if (const AActivityStation* Station = Cast<AActivityStation>(Focused))
            {
                const FString Uses = Station->RemainingUses < 0 ? TEXT("UNLIMITED")
                    : FString::FromInt(Station->RemainingUses);
                Prompt = FString::Printf(TEXT("[ E ]  %s  //  %s  //  %s  //  USES %s"),
                    *Station->Activity.DisplayName.ToString().ToUpper(),
                    *Station->OwningRoomCode.ToString(),
                    *Station->GetStationStatusText().ToString(), *Uses);
            }
            else
            {
                // What the thing says of itself first; then the ship system's name; the actor's
                // placement label only as a last resort (it reads "CVT_CRYOPOD_01").
                const FText Worded = Focused->Implements<UInteractable>()
                    ? IInteractable::Execute_GetInteractionPrompt(Focused, Cast<APawn>(OwningCharacter)) : FText::GetEmpty();
                const AShipSystemActor* System = Cast<AShipSystemActor>(Focused);
                const FString Name = !Worded.IsEmpty() ? Worded.ToString()
                    : (System && !System->SystemName.IsEmpty() ? System->SystemName : Focused->GetActorNameOrLabel());
                Prompt = FString::Printf(TEXT("[ E ]  %s"), *Name.ToUpper());
            }
        }
        SetInteractionPrompt(Prompt);
    }

    if (UGameInstance* GI = OwningCharacter->GetGameInstance())
    {
        if (UWorld* World = GI->GetWorld())
        {
            for (TActorIterator<AArmorPlatingSystem> It(World); It; ++It)
            {
                SetArmorStatus(It->ArmorIntegrity, It->bIsCorrupted);
                break;
            }
        }
    }
}

void USurvivalHUDWidget::SetCharacterName_Implementation(const FString& NewName)
{
    if (!CharacterNameText)
    {
        return;
    }

    // A profile with no name yet is still somebody: the suit's role, not a placeholder.
    const bool bUnnamed = NewName.IsEmpty() || NewName.Equals(TEXT("Unnamed"), ESearchCase::IgnoreCase);
    CharacterNameText->SetText(FText::FromString(bUnnamed ? TEXT("MARSHAL") : NewName));
}

void USurvivalHUDWidget::OnCharacterProfileChanged(const FCharacterProfile& NewProfile)
{
    SetCharacterName(NewProfile.CharacterName);
}
