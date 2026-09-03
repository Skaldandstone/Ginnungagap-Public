#include "Ship/ShipDamageComponent.h"
#include "Ship/ShipDamageControlSubsystem.h"
#include "Ship/ShipSection.h"
#include "Ship/ShipSystemActor.h"
#include "Ship/ShipPowerNodeComponent.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"

UShipDamageComponent::UShipDamageComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.25f;
    SetIsReplicatedByDefault(true);
}

void UShipDamageComponent::BeginPlay()
{
    Super::BeginPlay();
    if (UWorld* World = GetWorld())
    {
        if (UShipDamageControlSubsystem* DamageControl = World->GetSubsystem<UShipDamageControlSubsystem>())
        {
            DamageControl->RegisterDamageComponent(this);
        }
    }
}

void UShipDamageComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UWorld* World = GetWorld())
    {
        if (UShipDamageControlSubsystem* DamageControl = World->GetSubsystem<UShipDamageControlSubsystem>())
        {
            DamageControl->UnregisterDamageComponent(this);
        }
    }
    Super::EndPlay(EndPlayReason);
}

void UShipDamageComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (DeltaTime <= 0.0f) { return; }

    const float PreviousAtmosphere = AtmospherePercent;
    const float PreviousHull = HullIntegrity;
    if (BreachSeverity > 0.0f)
    {
        AtmospherePercent -= BreachSeverity * BreachAtmosphereLossPerSecond * DeltaTime;
    }
    else
    {
        AtmospherePercent += PassiveRepressurizationPerSecond * DeltaTime;
    }
    if (FireIntensity > 0.0f)
    {
        AtmospherePercent -= FireIntensity * FireAtmosphereLossPerSecond * DeltaTime;
        HullIntegrity -= FireIntensity * FireHullDamagePerSecond * DeltaTime;
    }
    AtmospherePercent = FMath::Clamp(AtmospherePercent, 0.0f, 100.0f);
    HullIntegrity = FMath::Clamp(HullIntegrity, 0.0f, 1.0f);

    if (!FMath::IsNearlyEqual(PreviousAtmosphere, AtmospherePercent) || !FMath::IsNearlyEqual(PreviousHull, HullIntegrity))
    {
        NotifyChanged();
    }
    UpdateAffectedShipSystems();
}

void UShipDamageComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UShipDamageComponent, HullIntegrity);
    DOREPLIFETIME(UShipDamageComponent, BreachSeverity);
    DOREPLIFETIME(UShipDamageComponent, FireIntensity);
    DOREPLIFETIME(UShipDamageComponent, ElectricalFaultSeverity);
    DOREPLIFETIME(UShipDamageComponent, AtmospherePercent);
}

void UShipDamageComponent::ApplyShipDamage(EShipDamageType DamageType, float Severity)
{
    Severity = FMath::Clamp(Severity, 0.0f, 1.0f);
    if (Severity <= 0.0f) { return; }

    switch (DamageType)
    {
    case EShipDamageType::HullImpact: HullIntegrity = FMath::Clamp(HullIntegrity - Severity, 0.0f, 1.0f); break;
    case EShipDamageType::Breach:
        BreachSeverity = FMath::Clamp(BreachSeverity + Severity, 0.0f, 1.0f);
        HullIntegrity = FMath::Clamp(HullIntegrity - Severity * 0.5f, 0.0f, 1.0f);
        break;
    case EShipDamageType::Fire: FireIntensity = FMath::Clamp(FireIntensity + Severity, 0.0f, 1.0f); break;
    case EShipDamageType::Electrical: ElectricalFaultSeverity = FMath::Clamp(ElectricalFaultSeverity + Severity, 0.0f, 1.0f); break;
    }
    NotifyChanged();
}

bool UShipDamageComponent::RepairHull(float RepairAmount)
{
    if (RepairAmount <= 0.0f || HullIntegrity >= 1.0f) { return false; }
    HullIntegrity = FMath::Clamp(HullIntegrity + RepairAmount, 0.0f, 1.0f); NotifyChanged(); return true;
}

bool UShipDamageComponent::SealBreach(float RepairAmount)
{
    if (RepairAmount <= 0.0f || BreachSeverity <= 0.0f) { return false; }
    BreachSeverity = FMath::Clamp(BreachSeverity - RepairAmount, 0.0f, 1.0f); NotifyChanged(); return true;
}

bool UShipDamageComponent::SuppressFire(float SuppressionAmount)
{
    if (SuppressionAmount <= 0.0f || FireIntensity <= 0.0f) { return false; }
    FireIntensity = FMath::Clamp(FireIntensity - SuppressionAmount, 0.0f, 1.0f); NotifyChanged(); return true;
}

bool UShipDamageComponent::RepairElectricalFault(float RepairAmount)
{
    if (RepairAmount <= 0.0f || ElectricalFaultSeverity <= 0.0f) { return false; }
    ElectricalFaultSeverity = FMath::Clamp(ElectricalFaultSeverity - RepairAmount, 0.0f, 1.0f); NotifyChanged(); UpdateAffectedShipSystems(); return true;
}

bool UShipDamageComponent::HasCriticalDamage() const
{
    return HullIntegrity <= 0.25f || BreachSeverity >= 0.75f || FireIntensity >= 0.75f || AtmospherePercent <= 20.0f;
}

float UShipDamageComponent::GetDangerScore() const
{
    return FMath::Clamp((1.0f - HullIntegrity) * 0.25f + BreachSeverity * 0.25f + FireIntensity * 0.25f
        + ElectricalFaultSeverity * 0.15f + (1.0f - AtmospherePercent / 100.0f) * 0.1f, 0.0f, 1.0f);
}

void UShipDamageComponent::OnRep_DamageState() { OnDamageStateChanged.Broadcast(); }
void UShipDamageComponent::NotifyChanged() { OnDamageStateChanged.Broadcast(); }

void UShipDamageComponent::UpdateAffectedShipSystems()
{
    const AShipSection* Section = Cast<AShipSection>(GetOwner());
    UWorld* World = GetWorld();
    if (!Section || !World) { return; }

    for (TActorIterator<AShipSystemActor> It(World); It; ++It)
    {
        if (Section->ContainsPoint(It->GetActorLocation()) && It->PowerNode)
        {
            It->PowerNode->SetDamageFraction(ElectricalFaultSeverity);
        }
    }
}

