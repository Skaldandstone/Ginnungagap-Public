#include "SensorArraySystem.h"
#include "../StarSystem/ShipResourceInventorySubsystem.h"
#include "Engine/GameInstance.h"
#include "../StarSystem/ProceduralStarSystemMap.h"
#include "EngineUtils.h"
#include "../UI/SensorSurveyWidget.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

ASensorArraySystem::ASensorArraySystem()
{
    SystemType = EShipSystemType::Sensors;
}

bool ASensorArraySystem::UpgradeShortRange()
{
    if (ShortRangeLevel >= MaxSensorLevel)
    {
        return false;
    }

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UShipResourceInventorySubsystem* Inventory = GI->GetSubsystem<UShipResourceInventorySubsystem>())
        {
            if (Inventory->TrySpendResource(EStarSystemResourceType::SensorComponents, UpgradeCostSensorComponents))
            {
                ShortRangeLevel += 1;
                return true;
            }
        }
    }

    return false;
}

bool ASensorArraySystem::UpgradeLongRange()
{
    if (LongRangeLevel >= MaxSensorLevel)
    {
        return false;
    }

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UShipResourceInventorySubsystem* Inventory = GI->GetSubsystem<UShipResourceInventorySubsystem>())
        {
            if (Inventory->TrySpendResource(EStarSystemResourceType::SensorComponents, UpgradeCostSensorComponents))
            {
                LongRangeLevel += 1;
                return true;
            }
        }
    }

    return false;
}

float ASensorArraySystem::GetCandidateRevealFraction() const
{
    return MaxSensorLevel > 0 ? FMath::Clamp(static_cast<float>(ShortRangeLevel) / static_cast<float>(MaxSensorLevel), 0.0f, 1.0f) : 0.0f;
}

float ASensorArraySystem::GetFalsificationResistance() const
{
    const float LevelResistance = MaxSensorLevel > 1
        ? FMath::Clamp(1.0f - (static_cast<float>(LongRangeLevel - 1) / static_cast<float>(MaxSensorLevel - 1)) * 0.5f, 0.5f, 1.0f)
        : 1.0f;

    return bIsCorrupted ? FMath::Lerp(LevelResistance, 1.0f, 0.7f) : LevelResistance;
}

TArray<FSensorContact> ASensorArraySystem::ScanCurrentSystem() const
{
    TArray<FSensorContact> Contacts;
    UWorld* World = GetWorld();
    if (!World)
    {
        return Contacts;
    }

    const AProceduralStarSystemMap* SystemMap = nullptr;
    for (TActorIterator<AProceduralStarSystemMap> It(World); It; ++It)
    {
        SystemMap = *It;
        break;
    }
    if (!SystemMap)
    {
        return Contacts;
    }

    const float EffectiveRange = ScanRangePerLongRangeLevel * FMath::Max(1, LongRangeLevel) * (bIsCorrupted ? 0.55f : 1.0f);
    const float IdentificationPower = MaxSensorLevel > 0 ? static_cast<float>(ShortRangeLevel) / MaxSensorLevel : 0.0f;
    const FVector SensorLocation = GetActorLocation();
    const FVector Forward = GetActorForwardVector();

    for (const FSystemPointOfInterest& Point : SystemMap->PointsOfInterest)
    {
        const FVector Offset = Point.WorldLocation - SensorLocation;
        const float Distance = Offset.Size();
        if (Point.SensorSignature <= 0.0f || Distance > EffectiveRange * FMath::Lerp(0.45f, 1.0f, Point.SensorSignature))
        {
            continue;
        }

        FSensorContact Contact;
        Contact.WorldLocation = Point.WorldLocation;
        Contact.DistanceKilometers = Distance / 100000.0f;
        const FVector FlatOffset(Offset.X, Offset.Y, 0.0f);
        const FVector FlatForward(Forward.X, Forward.Y, 0.0f);
        Contact.BearingDegrees = FlatOffset.IsNearlyZero() || FlatForward.IsNearlyZero()
            ? 0.0f
            : FMath::RadiansToDegrees(FMath::Atan2(FVector::CrossProduct(FlatForward.GetSafeNormal(), FlatOffset.GetSafeNormal()).Z,
                                                    FVector::DotProduct(FlatForward.GetSafeNormal(), FlatOffset.GetSafeNormal())));
        const float IdentificationThreshold = FMath::Clamp(0.72f - IdentificationPower * 0.55f, 0.12f, 0.72f);
        Contact.bIdentified = Point.SensorSignature >= IdentificationThreshold || Point.Type == ESystemPointOfInterestType::Arrival;
        Contact.DisplayName = Contact.bIdentified ? Point.Name : FName(TEXT("Unknown Contact"));
        Contact.Type = Contact.bIdentified ? Point.Type : ESystemPointOfInterestType::Unknown;
        Contact.bCriticalResource = Contact.bIdentified && Point.bCriticalResource;
        Contacts.Add(Contact);
    }

    Contacts.Sort([](const FSensorContact& A, const FSensorContact& B)
    {
        return A.DistanceKilometers < B.DistanceKilometers;
    });
    return Contacts;
}

void ASensorArraySystem::TrackContact(const FSensorContact& Contact)
{
    TrackedContact = Contact;
    bHasTrackedContact = true;
    OnTrackedContactChanged(true, TrackedContact);
}

bool ASensorArraySystem::TrackNearestCriticalResource()
{
    for (const FSensorContact& Contact : ScanCurrentSystem())
    {
        if (Contact.bCriticalResource && Contact.Type == ESystemPointOfInterestType::Resource)
        {
            TrackContact(Contact);
            return true;
        }
    }
    return false;
}

void ASensorArraySystem::ClearTrackedContact()
{
    bHasTrackedContact = false;
    TrackedContact = FSensorContact();
    OnTrackedContactChanged(false, TrackedContact);
}

FSensorContact ASensorArraySystem::GetTrackedContact()
{
    FSensorContact Result = TrackedContact;
    if (!bHasTrackedContact)
    {
        return Result;
    }

    bool bContactStillExists = false;
    for (const FSensorContact& LiveContact : ScanCurrentSystem())
    {
        if (LiveContact.DisplayName == Result.DisplayName && LiveContact.Type == Result.Type)
        {
            Result.WorldLocation = LiveContact.WorldLocation;
            bContactStillExists = true;
            break;
        }
    }
    if (!bContactStillExists)
    {
        ClearTrackedContact();
        return FSensorContact();
    }
    const FVector Offset = Result.WorldLocation - GetActorLocation();
    Result.DistanceKilometers = Offset.Size() / 100000.0f;
    const FVector FlatOffset(Offset.X, Offset.Y, 0.0f);
    const FVector FlatForward(GetActorForwardVector().X, GetActorForwardVector().Y, 0.0f);
    if (!FlatOffset.IsNearlyZero() && !FlatForward.IsNearlyZero())
    {
        Result.BearingDegrees = FMath::RadiansToDegrees(FMath::Atan2(
            FVector::CrossProduct(FlatForward.GetSafeNormal(), FlatOffset.GetSafeNormal()).Z,
            FVector::DotProduct(FlatForward.GetSafeNormal(), FlatOffset.GetSafeNormal())));
    }
    return Result;
}

void ASensorArraySystem::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (ActiveSurveyWidget && ActiveSurveyWidget->IsInViewport())
    {
        ActiveSurveyWidget->RemoveFromParent();
        return;
    }

    APlayerController* PlayerController = InteractingPawn ? Cast<APlayerController>(InteractingPawn->GetController()) : nullptr;
    if (PlayerController)
    {
        ActiveSurveyWidget = CreateWidget<USensorSurveyWidget>(PlayerController, USensorSurveyWidget::StaticClass());
        if (ActiveSurveyWidget)
        {
            ActiveSurveyWidget->SetSensorSource(this);
            ActiveSurveyWidget->AddToViewport(40);
        }
    }
    OnSensorConsoleOpened();
}

void ASensorArraySystem::OnSensorConsoleOpened_Implementation()
{
}

void ASensorArraySystem::ApplyCorruptionEffects()
{
    // Sensors stay online while corrupted - GetFalsificationResistance() reacts to bIsCorrupted directly.
}

void ASensorArraySystem::RemoveCorruptionEffects()
{
}
