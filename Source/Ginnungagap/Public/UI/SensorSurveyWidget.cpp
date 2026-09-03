#include "SensorSurveyWidget.h"

#include "Components/Border.h"
#include "Components/ScrollBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Button.h"
#include "Blueprint/WidgetTree.h"
#include "Ship/SensorArraySystem.h"
#include "SensorContactRowWidget.h"
#include "Ship/ShipHelmSystem.h"
#include "StarSystem/ResourceNodeActor.h"
#include "StarSystem/DormantCollectorSystem.h"
#include "StarSystem/RetrievalDroneActor.h"
#include "StarSystem/JumpSequenceSubsystem.h"
#include "StarSystem/ShipResourceInventorySubsystem.h"
#include "StarSystem/ProceduralStarSystemMap.h"
#include "EngineUtils.h"

void USensorSurveyWidget::NativeConstruct()
{
    Super::NativeConstruct();
    BuildWidgetTree();
    if (UGameInstance* GI = GetGameInstance())
    {
        CachedInventory = GI->GetSubsystem<UShipResourceInventorySubsystem>();
        if (CachedInventory)
        {
            CachedInventory->OnResourceChanged.AddUniqueDynamic(this, &USensorSurveyWidget::HandleResourceChanged);
        }
    }
    RefreshInventoryDisplay();
    RefreshContacts();
}

void USensorSurveyWidget::NativeDestruct()
{
    if (CachedInventory)
    {
        CachedInventory->OnResourceChanged.RemoveDynamic(this, &USensorSurveyWidget::HandleResourceChanged);
    }
    Super::NativeDestruct();
}

void USensorSurveyWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    RefreshAccumulator += InDeltaTime;
    if (RefreshAccumulator >= RefreshInterval)
    {
        RefreshAccumulator = 0.0f;
        RefreshContacts();
    }
}

void USensorSurveyWidget::SetSensorSource(ASensorArraySystem* InSensorSource)
{
    SensorSource = InSensorSource;
    RefreshContacts();
}

void USensorSurveyWidget::BuildWidgetTree()
{
    if (!WidgetTree || WidgetTree->RootWidget)
    {
        return;
    }

    UBorder* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("SurveyFrame"));
    Frame->SetBrushColor(FLinearColor(0.008f, 0.018f, 0.025f, 0.96f));
    Frame->SetPadding(FMargin(24.0f));
    WidgetTree->RootWidget = Frame;

    UVerticalBox* Layout = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("SurveyLayout"));
    Frame->SetContent(Layout);

    UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SurveyTitle"));
    Title->SetText(FText::FromString(TEXT("SYSTEM SURVEY // ACTIVE CONTACTS")));
    Title->SetColorAndOpacity(FSlateColor(FLinearColor(0.35f, 0.85f, 1.0f)));
    Layout->AddChildToVerticalBox(Title)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 12.0f));

    SystemIdentityText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SystemIdentity"));
    SystemIdentityText->SetColorAndOpacity(FSlateColor(FLinearColor(0.75f, 0.86f, 1.0f)));
    SystemIdentityText->SetText(FText::FromString(TEXT("SYSTEM DATA PENDING")));
    Layout->AddChildToVerticalBox(SystemIdentityText)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 7.0f));

    StatusText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SurveyStatus"));
    StatusText->SetColorAndOpacity(FSlateColor(FLinearColor(0.65f, 0.75f, 0.78f)));
    Layout->AddChildToVerticalBox(StatusText)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));

    InventoryText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ShipInventory"));
    InventoryText->SetColorAndOpacity(FSlateColor(FLinearColor(0.72f, 0.82f, 0.86f)));
    Layout->AddChildToVerticalBox(InventoryText)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 5.0f));

    ResourceResultText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ResourceResult"));
    ResourceResultText->SetColorAndOpacity(FSlateColor(FLinearColor(0.3f, 1.0f, 0.55f)));
    ResourceResultText->SetVisibility(ESlateVisibility::Collapsed);
    Layout->AddChildToVerticalBox(ResourceResultText)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));

    TrackPriorityButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("TrackPriorityButton"));
    UTextBlock* PriorityLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("TrackPriorityLabel"));
    PriorityLabel->SetText(FText::FromString(TEXT("TRACK NEAREST PRIORITY RESOURCE")));
    PriorityLabel->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.25f, 0.12f)));
    TrackPriorityButton->AddChild(PriorityLabel);
    TrackPriorityButton->OnClicked.AddDynamic(this, &USensorSurveyWidget::HandleTrackPriorityClicked);
    TrackPriorityButton->SetVisibility(ESlateVisibility::Collapsed);
    Layout->AddChildToVerticalBox(TrackPriorityButton)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));

    HeadingAssistButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("HeadingAssistButton"));
    HeadingAssistLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("HeadingAssistLabel"));
    HeadingAssistLabel->SetText(FText::FromString(TEXT("ENGAGE HELM ASSIST")));
    HeadingAssistLabel->SetColorAndOpacity(FSlateColor(FLinearColor(0.35f, 0.85f, 1.0f)));
    HeadingAssistButton->AddChild(HeadingAssistLabel);
    HeadingAssistButton->OnClicked.AddDynamic(this, &USensorSurveyWidget::HandleHeadingAssistClicked);
    HeadingAssistButton->SetVisibility(ESlateVisibility::Collapsed);
    Layout->AddChildToVerticalBox(HeadingAssistButton)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));

    CoursePreviewText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("CoursePreview"));
    CoursePreviewText->SetColorAndOpacity(FSlateColor(FLinearColor(0.55f, 0.78f, 0.86f)));
    CoursePreviewText->SetVisibility(ESlateVisibility::Collapsed);
    Layout->AddChildToVerticalBox(CoursePreviewText)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));

    HeadingCorrectionButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("HeadingCorrectionButton"));
    UTextBlock* CorrectionLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("HeadingCorrectionLabel"));
    CorrectionLabel->SetText(FText::FromString(FString::Printf(TEXT("EXECUTE CORRECTION BURN // %d FUEL"), HeadingCorrectionFuelCost)));
    CorrectionLabel->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.7f, 0.2f)));
    HeadingCorrectionButton->AddChild(CorrectionLabel);
    HeadingCorrectionButton->OnClicked.AddDynamic(this, &USensorSurveyWidget::HandleHeadingCorrectionClicked);
    HeadingCorrectionButton->SetVisibility(ESlateVisibility::Collapsed);
    Layout->AddChildToVerticalBox(HeadingCorrectionButton)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));

    OperationsText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("OperationsStatus"));
    OperationsText->SetColorAndOpacity(FSlateColor(FLinearColor(0.3f, 1.0f, 0.55f)));
    OperationsText->SetVisibility(ESlateVisibility::Collapsed);
    Layout->AddChildToVerticalBox(OperationsText)->SetPadding(FMargin(0.0f, 4.0f, 0.0f, 6.0f));

    DispatchDroneButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("DispatchDroneButton"));
    UTextBlock* DispatchLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("DispatchDroneLabel"));
    DispatchLabel->SetText(FText::FromString(TEXT("DISPATCH RETRIEVAL DRONE")));
    DispatchDroneButton->AddChild(DispatchLabel);
    DispatchDroneButton->OnClicked.AddDynamic(this, &USensorSurveyWidget::HandleDispatchDroneClicked);
    DispatchDroneButton->SetVisibility(ESlateVisibility::Collapsed);
    Layout->AddChildToVerticalBox(DispatchDroneButton)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 10.0f));

    EVAOperationButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("EVAOperationButton"));
    UTextBlock* EVALabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("EVAOperationLabel"));
    EVALabel->SetText(FText::FromString(TEXT("RECOVER RESOURCE // EVA")));
    EVAOperationButton->AddChild(EVALabel);
    EVAOperationButton->OnClicked.AddDynamic(this, &USensorSurveyWidget::HandleEVAOperationClicked);
    EVAOperationButton->SetVisibility(ESlateVisibility::Collapsed);
    Layout->AddChildToVerticalBox(EVAOperationButton)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 10.0f));

    CollectorOperationButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("CollectorOperationButton"));
    CollectorOperationLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("CollectorOperationLabel"));
    CollectorOperationButton->AddChild(CollectorOperationLabel);
    CollectorOperationButton->OnClicked.AddDynamic(this, &USensorSurveyWidget::HandleCollectorOperationClicked);
    CollectorOperationButton->SetVisibility(ESlateVisibility::Collapsed);
    Layout->AddChildToVerticalBox(CollectorOperationButton)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 10.0f));

    DroneStatusText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("DroneStatus"));
    DroneStatusText->SetColorAndOpacity(FSlateColor(FLinearColor(0.35f, 0.85f, 1.0f)));
    DroneStatusText->SetVisibility(ESlateVisibility::Collapsed);
    Layout->AddChildToVerticalBox(DroneStatusText)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));

    ContactList = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(), TEXT("ContactList"));
    UVerticalBoxSlot* ListSlot = Layout->AddChildToVerticalBox(ContactList);
    ListSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
}

void USensorSurveyWidget::RefreshInventoryDisplay()
{
    if (!InventoryText || !CachedInventory)
    {
        return;
    }
    InventoryText->SetText(FText::FromString(FString::Printf(
        TEXT("SHIP STORES // FUEL %d  ALLOY %d  COOLANT %d  FILTERS %d  SENSORS %d  CELLS %d"),
        CachedInventory->GetResourceAmount(EStarSystemResourceType::NavigationFuel),
        CachedInventory->GetResourceAmount(EStarSystemResourceType::StructuralAlloy),
        CachedInventory->GetResourceAmount(EStarSystemResourceType::CryoCoolant),
        CachedInventory->GetResourceAmount(EStarSystemResourceType::LifeSupportFilters),
        CachedInventory->GetResourceAmount(EStarSystemResourceType::SensorComponents),
        CachedInventory->GetResourceAmount(EStarSystemResourceType::PowerCells))));
}

void USensorSurveyWidget::HandleResourceChanged(EStarSystemResourceType ResourceType, int32 NewAmount, int32 Delta)
{
    static const TCHAR* ResourceNames[] = {TEXT("NAVIGATION FUEL"), TEXT("STRUCTURAL ALLOY"), TEXT("CRYO COOLANT"),
        TEXT("LIFE SUPPORT FILTERS"), TEXT("SENSOR COMPONENTS"), TEXT("POWER CELLS")};
    RefreshInventoryDisplay();
    if (ResourceResultText && Delta != 0)
    {
        ResourceResultText->SetVisibility(ESlateVisibility::Visible);
        ResourceResultText->SetColorAndOpacity(FSlateColor(Delta > 0 ? FLinearColor(0.3f, 1.0f, 0.55f) : FLinearColor(1.0f, 0.7f, 0.2f)));
        ResourceResultText->SetText(FText::FromString(FString::Printf(TEXT("%s // %s %d // TOTAL %d"),
            Delta > 0 ? TEXT("CARGO SECURED") : TEXT("STORES EXPENDED"),
            ResourceNames[static_cast<int32>(ResourceType)], FMath::Abs(Delta), NewAmount)));
    }
}

void USensorSurveyWidget::RefreshContacts()
{
    if (!ContactList || !StatusText)
    {
        return;
    }
    ContactList->ClearChildren();
    if (!SensorSource)
    {
        StatusText->SetText(FText::FromString(TEXT("NO SENSOR ARRAY LINK")));
        return;
    }

    const TArray<FSensorContact> Contacts = SensorSource->ScanCurrentSystem();
    const AProceduralStarSystemMap* SystemMap = nullptr;
    for (TActorIterator<AProceduralStarSystemMap> It(GetWorld()); It; ++It)
    {
        SystemMap = *It;
        break;
    }
    const int32 RecoveredResources = SystemMap ? SystemMap->GetRecoveredResourceContactCount() : 0;
    const int32 TotalResources = SystemMap ? SystemMap->GeneratedSystem.Resources.Num() : 0;
    int32 CriticalRemaining = 0;
    for (const FSensorContact& Contact : Contacts)
    {
        CriticalRemaining += Contact.bCriticalResource ? 1 : 0;
    }
    if (TrackPriorityButton)
    {
        TrackPriorityButton->SetVisibility(CriticalRemaining > 0 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    }
    const TCHAR* SweepState = SystemMap && SystemMap->IsResourceSweepComplete() ? TEXT("  //  RESOURCE SWEEP COMPLETE") : TEXT("");
    if (SystemIdentityText)
    {
        static const TCHAR* PhenomenonNames[] = {
            TEXT("GOLDEN GIANT"), TEXT("BLUE-WHITE STAR"), TEXT("BINARY STARS"), TEXT("VIOLET DWARF"),
            TEXT("ION NEBULA"), TEXT("GRAVITY ANOMALY"), TEXT("FRACTURED WORLD")};
        if (SystemMap)
        {
            const int32 DangerTier = SystemMap->GeneratedSystem.DangerTier;
            SystemIdentityText->SetColorAndOpacity(FSlateColor(DangerTier >= 4
                ? FLinearColor(1.0f, 0.25f, 0.12f) : (DangerTier >= 2
                    ? FLinearColor(1.0f, 0.7f, 0.2f) : FLinearColor(0.75f, 0.86f, 1.0f))));
            SystemIdentityText->SetText(FText::FromString(FString::Printf(TEXT("%s  //  %s  //  DANGER TIER %d"),
                *SystemMap->GeneratedSystem.DisplayName.ToUpper(),
                PhenomenonNames[static_cast<int32>(SystemMap->DominantPhenomenon)], DangerTier)));
        }
        else
        {
            SystemIdentityText->SetText(FText::FromString(TEXT("NO GENERATED SYSTEM MAP DETECTED")));
            SystemIdentityText->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.25f, 0.12f)));
        }
    }
    StatusText->SetColorAndOpacity(FSlateColor(SystemMap && SystemMap->IsResourceSweepComplete()
        ? FLinearColor(0.3f, 1.0f, 0.55f) : FLinearColor(0.65f, 0.75f, 0.78f)));
    StatusText->SetText(FText::FromString(FString::Printf(TEXT("SR %d  LR %d  //  %d CONTACTS  //  RECOVERY %d/%d  //  PRIORITY %d%s%s"),
        SensorSource->ShortRangeLevel, SensorSource->LongRangeLevel, Contacts.Num(), RecoveredResources, TotalResources,
        CriticalRemaining, SensorSource->bIsCorrupted ? TEXT("  //  SIGNAL COMPROMISED") : TEXT(""), SweepState)));

    if (!CachedHelm)
    {
        for (TActorIterator<AShipHelmSystem> It(GetWorld()); It; ++It)
        {
            CachedHelm = *It;
            break;
        }
    }
    if (HeadingAssistButton && HeadingAssistLabel)
    {
        const bool bCanNavigate = CachedHelm && SensorSource->HasTrackedContact();
        HeadingAssistButton->SetVisibility(bCanNavigate ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        if (bCanNavigate)
        {
            HeadingAssistLabel->SetText(FText::FromString(CachedHelm->bHeadingAssistActive
                ? TEXT("DISENGAGE HELM ASSIST") : TEXT("ENGAGE HELM ASSIST")));
            HeadingAssistLabel->SetColorAndOpacity(FSlateColor(CachedHelm->bHeadingAssistActive
                ? FLinearColor(0.3f, 1.0f, 0.55f) : FLinearColor(0.35f, 0.85f, 1.0f)));
        }
    }
    if (CoursePreviewText)
    {
        const bool bHasCourse = CachedHelm && SensorSource->HasTrackedContact();
        CoursePreviewText->SetVisibility(bHasCourse ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        if (bHasCourse)
        {
            const FHelmNavigationSolution Solution = CachedHelm->UpdateTrackedContactSolution();
            const TCHAR* RouteState = Solution.bUsingSafeDetour ? TEXT("SAFE DETOUR")
                : (Solution.bRouteIntersectsHazard ? TEXT("HAZARD INTERSECTION") : TEXT("CLEAR"));
            const TCHAR* FlightState = Solution.bBraking ? TEXT("ARRIVAL BURN")
                : (CachedHelm->bHeadingAssistActive ? TEXT("UNDERWAY") : TEXT("STANDBY"));
            CoursePreviewText->SetColorAndOpacity(FSlateColor(Solution.bRouteIntersectsHazard && !Solution.bUsingSafeDetour
                ? FLinearColor(1.0f, 0.25f, 0.12f) : FLinearColor(0.55f, 0.78f, 0.86f)));
            CoursePreviewText->SetText(FText::FromString(FString::Printf(
                TEXT("COURSE // RANGE %.1f km  ETA %.0f s  ERROR %.1f deg  //  %s  //  %s"),
                Solution.RangeKilometers, Solution.EstimatedTravelSeconds, Solution.HeadingErrorDegrees,
                RouteState, FlightState)));
            if (HeadingCorrectionButton)
            {
                HeadingCorrectionButton->SetVisibility(FMath::Abs(Solution.HeadingErrorDegrees) >= HeadingCorrectionThresholdDegrees
                    ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
                HeadingCorrectionButton->SetIsEnabled(CachedInventory &&
                    CachedInventory->GetResourceAmount(EStarSystemResourceType::NavigationFuel) >= HeadingCorrectionFuelCost);
            }
        }
        else if (HeadingCorrectionButton)
        {
            HeadingCorrectionButton->SetVisibility(ESlateVisibility::Collapsed);
        }
    }
    AResourceNodeActor* Resource = CachedHelm && IsValid(CachedHelm->ActiveOperationsTarget)
        ? Cast<AResourceNodeActor>(CachedHelm->ActiveOperationsTarget) : nullptr;
    if (OperationsText && DispatchDroneButton && EVAOperationButton && CollectorOperationButton)
    {
        OperationsText->SetVisibility(Resource ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        DispatchDroneButton->SetVisibility(Resource && Resource->bShipOnStation &&
            Resource->RequiredMethod == EResourceAcquisitionMethod::DroneDispatch ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        const bool bEVAOperation = Resource && Resource->bShipOnStation &&
            Resource->RequiredMethod == EResourceAcquisitionMethod::EVARetrieval;
        EVAOperationButton->SetVisibility(bEVAOperation ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        EVAOperationButton->SetIsEnabled(bEVAOperation && Resource->CanBeCollectedBy(GetOwningPlayerPawn()));

        const bool bCollectorOperation = Resource && Resource->bShipOnStation &&
            Resource->RequiredMethod == EResourceAcquisitionMethod::ShipSystemReactivation;
        CollectorOperationButton->SetVisibility(bCollectorOperation ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        if (bCollectorOperation)
        {
            const ADormantCollectorSystem* Collector = Cast<ADormantCollectorSystem>(Resource->RequiredSystem);
            const bool bReady = Resource->CanBeCollectedBy(GetOwningPlayerPawn());
            const bool bActivating = Collector && Collector->IsReactivating();
            CollectorOperationButton->SetIsEnabled(bReady || (Collector && Collector->CanBeginReactivation()));
            CollectorOperationLabel->SetText(FText::FromString(bReady ? TEXT("TRANSFER COLLECTOR YIELD")
                : (bActivating ? TEXT("COLLECTOR REACTIVATION IN PROGRESS") : TEXT("REACTIVATE SHIP COLLECTOR"))));
        }
        if (Resource)
        {
            static const TCHAR* ResourceNames[] = {TEXT("NAVIGATION FUEL"), TEXT("STRUCTURAL ALLOY"), TEXT("CRYO COOLANT"),
                TEXT("LIFE SUPPORT FILTERS"), TEXT("SENSOR COMPONENTS"), TEXT("POWER CELLS")};
            static const TCHAR* MethodNames[] = {TEXT("COLLECTOR REACTIVATION"), TEXT("EVA RETRIEVAL"), TEXT("DRONE DISPATCH")};
            OperationsText->SetText(FText::FromString(FString::Printf(TEXT("ON STATION // %s x%d // %s"),
                ResourceNames[static_cast<int32>(Resource->ResourceType)], Resource->Quantity,
                MethodNames[static_cast<int32>(Resource->RequiredMethod)])));
        }
    }


    if (DroneStatusText)
    {
        ARetrievalDroneActor* ActiveDrone = nullptr;
        for (TActorIterator<ARetrievalDroneActor> It(GetWorld()); It; ++It)
        {
            if (It->CurrentState != EDroneState::Docked)
            {
                ActiveDrone = *It;
                if (It->CurrentState != EDroneState::Returned && It->CurrentState != EDroneState::Lost)
                {
                    break;
                }
            }
        }
        DroneStatusText->SetVisibility(ActiveDrone ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        if (ActiveDrone)
        {
            static const TCHAR* StateNames[] = {TEXT("DOCKED"), TEXT("OUTBOUND"), TEXT("COLLECTING"), TEXT("RETURNING"), TEXT("CARGO SECURED"), TEXT("DRONE LOST")};
            const bool bLost = ActiveDrone->CurrentState == EDroneState::Lost;
            DroneStatusText->SetColorAndOpacity(FSlateColor(bLost ? FLinearColor(1.0f, 0.18f, 0.08f) : FLinearColor(0.35f, 0.85f, 1.0f)));
            DroneStatusText->SetText(FText::FromString(FString::Printf(TEXT("DRONE // %s // %3.0f%%"),
                StateNames[static_cast<int32>(ActiveDrone->CurrentState)], ActiveDrone->GetStateProgress() * 100.0f)));
        }
    }

    for (const FSensorContact& Contact : Contacts)
    {
        USensorContactRowWidget* Row = CreateWidget<USensorContactRowWidget>(GetOwningPlayer(), USensorContactRowWidget::StaticClass());
        const bool bTracked = SensorSource->HasTrackedContact() && SensorSource->GetTrackedContact().WorldLocation.Equals(Contact.WorldLocation, 1.0f);
        Row->Configure(SensorSource, Contact, bTracked);
        ContactList->AddChild(Row);
    }
}

void USensorSurveyWidget::HandleDispatchDroneClicked()
{
    DispatchDroneOperation();
}

void USensorSurveyWidget::HandleEVAOperationClicked()
{
    if (!PerformEVAOperation() && ResourceResultText)
    {
        ResourceResultText->SetVisibility(ESlateVisibility::Visible);
        ResourceResultText->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.7f, 0.2f)));
        ResourceResultText->SetText(FText::FromString(TEXT("EVA RECOVERY LOCKED // EXIT SHIP AND REOPEN SENSOR LINK")));
    }
    RefreshContacts();
}

void USensorSurveyWidget::HandleCollectorOperationClicked()
{
    if (!PerformCollectorOperation() && ResourceResultText)
    {
        ResourceResultText->SetVisibility(ESlateVisibility::Visible);
        ResourceResultText->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.25f, 0.12f)));
        ResourceResultText->SetText(FText::FromString(TEXT("COLLECTOR OPERATION ABORTED // SYSTEM UNAVAILABLE")));
    }
    RefreshContacts();
}

void USensorSurveyWidget::HandleTrackPriorityClicked()
{
    if (SensorSource && SensorSource->TrackNearestCriticalResource())
    {
        RefreshContacts();
    }
}

void USensorSurveyWidget::HandleHeadingAssistClicked()
{
    if (!CachedHelm || !SensorSource || !SensorSource->HasTrackedContact())
    {
        return;
    }

    if (CachedHelm->bHeadingAssistActive)
    {
        CachedHelm->EndHeadingAssist();
        if (ResourceResultText)
        {
            ResourceResultText->SetVisibility(ESlateVisibility::Visible);
            ResourceResultText->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.7f, 0.2f)));
            ResourceResultText->SetText(FText::FromString(TEXT("HELM ASSIST DISENGAGED")));
        }
    }
    else
    {
        const bool bEngaged = CachedHelm->BeginHeadingAssist();
        if (ResourceResultText)
        {
            ResourceResultText->SetVisibility(ESlateVisibility::Visible);
            ResourceResultText->SetColorAndOpacity(FSlateColor(bEngaged
                ? FLinearColor(0.3f, 1.0f, 0.55f) : FLinearColor(1.0f, 0.25f, 0.12f)));
            ResourceResultText->SetText(FText::FromString(bEngaged
                ? TEXT("HELM ASSIST ENGAGED // COURSE ACCEPTED")
                : TEXT("COURSE REJECTED // HAZARD OR HELM FAULT")));
        }
    }
    RefreshContacts();
}

void USensorSurveyWidget::HandleHeadingCorrectionClicked()
{
    if (!CachedInventory || !CachedHelm)
    {
        return;
    }

    const bool bCorrected = CachedInventory->TrySpendForHeadingCorrection(CachedHelm, 1.0f, HeadingCorrectionFuelCost);
    if (!bCorrected && ResourceResultText)
    {
        ResourceResultText->SetVisibility(ESlateVisibility::Visible);
        ResourceResultText->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.25f, 0.12f)));
        ResourceResultText->SetText(FText::FromString(TEXT("CORRECTION BURN ABORTED // INSUFFICIENT NAVIGATION FUEL")));
    }
    RefreshContacts();
}

bool USensorSurveyWidget::DispatchDroneOperation()
{
    AResourceNodeActor* Resource = CachedHelm && IsValid(CachedHelm->ActiveOperationsTarget)
        ? Cast<AResourceNodeActor>(CachedHelm->ActiveOperationsTarget) : nullptr;
    if (!Resource || !Resource->bShipOnStation || Resource->RequiredMethod != EResourceAcquisitionMethod::DroneDispatch)
    {
        return false;
    }

    ARetrievalDroneActor* AvailableDrone = nullptr;
    for (TActorIterator<ARetrievalDroneActor> It(GetWorld()); It; ++It)
    {
        if (It->CurrentState == EDroneState::Docked || It->CurrentState == EDroneState::Returned)
        {
            AvailableDrone = *It;
            break;
        }
    }
    if (!AvailableDrone)
    {
        return false;
    }

    float HazardSeverity = 0.0f;
    if (UGameInstance* GI = GetGameInstance())
    {
        if (UJumpSequenceSubsystem* Jump = GI->GetSubsystem<UJumpSequenceSubsystem>())
        {
            for (const FHazardEntry& Hazard : Jump->CurrentSystemData.Hazards)
            {
                HazardSeverity = FMath::Max(HazardSeverity, Hazard.Severity);
            }
        }
    }
    return AvailableDrone->DispatchTo(Resource, HazardSeverity);
}

bool USensorSurveyWidget::PerformEVAOperation()
{
    AResourceNodeActor* Resource = CachedHelm && IsValid(CachedHelm->ActiveOperationsTarget)
        ? Cast<AResourceNodeActor>(CachedHelm->ActiveOperationsTarget) : nullptr;
    APawn* Pawn = GetOwningPlayerPawn();
    if (!Resource || Resource->RequiredMethod != EResourceAcquisitionMethod::EVARetrieval ||
        !CanExecuteDirectResourceOperation(Resource->RequiredMethod, Resource->bShipOnStation,
            Resource->CanBeCollectedBy(Pawn)))
    {
        return false;
    }

    Resource->OnInteract_Implementation(Pawn);
    return true;
}

bool USensorSurveyWidget::PerformCollectorOperation()
{
    AResourceNodeActor* Resource = CachedHelm && IsValid(CachedHelm->ActiveOperationsTarget)
        ? Cast<AResourceNodeActor>(CachedHelm->ActiveOperationsTarget) : nullptr;
    APawn* Pawn = GetOwningPlayerPawn();
    if (!Resource || !Pawn || !Resource->bShipOnStation ||
        Resource->RequiredMethod != EResourceAcquisitionMethod::ShipSystemReactivation)
    {
        return false;
    }

    if (CanExecuteDirectResourceOperation(Resource->RequiredMethod, Resource->bShipOnStation,
        Resource->CanBeCollectedBy(Pawn)))
    {
        Resource->OnInteract_Implementation(Pawn);
        return true;
    }

    ADormantCollectorSystem* Collector = Cast<ADormantCollectorSystem>(Resource->RequiredSystem);
    if (!Collector || !Collector->CanBeginReactivation())
    {
        return false;
    }

    Collector->OnInteract_Implementation(Pawn);
    return true;
}

bool USensorSurveyWidget::CanExecuteDirectResourceOperation(EResourceAcquisitionMethod Method,
    bool bShipOnStation, bool bAcquisitionRequirementSatisfied)
{
    return bShipOnStation && bAcquisitionRequirementSatisfied &&
        Method != EResourceAcquisitionMethod::DroneDispatch;
}
