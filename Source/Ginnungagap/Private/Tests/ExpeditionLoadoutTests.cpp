#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "Equipment/ExpeditionLoadoutSubsystem.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FExpeditionLoadoutRulesTest,
	"Ginnungagap.UI.PreGameLoadout.Rules",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FExpeditionLoadoutRulesTest::RunTest(const FString& Parameters)
{
	UGameInstance* GameInstance = NewObject<UGameInstance>();
	UExpeditionLoadoutSubsystem* Loadout = NewObject<UExpeditionLoadoutSubsystem>(GameInstance);
	Loadout->ResetToStarterLoadout();

	TestEqual(TEXT("Quartermaster catalog contains six authored options"), Loadout->GetEquipmentCatalog().Num(), 6);
	TestEqual(TEXT("Starter kit uses four supply"), Loadout->GetUsedSupply(), 4);
	TestTrue(TEXT("Starter kit includes the survey visor"), Loadout->IsEquipmentSelected(EEquipmentType::HelmetVisor));
	TestTrue(TEXT("Starter kit includes the pressure seal kit"), Loadout->IsEquipmentSelected(EEquipmentType::PressureSeal));
	TestTrue(TEXT("Starter kit includes the scrubber pack"), Loadout->IsEquipmentSelected(EEquipmentType::OxygenFilter));

	TestTrue(TEXT("Thermal plating fits the remaining budget"), Loadout->ToggleEquipment(EEquipmentType::ThermalPlating));
	TestEqual(TEXT("Thermal loadout uses seven supply"), Loadout->GetUsedSupply(), 7);
	TestTrue(TEXT("Same-slot armor replaces thermal plating"), Loadout->ToggleEquipment(EEquipmentType::ArmorPlating));
	TestFalse(TEXT("Replaced thermal plating is no longer selected"), Loadout->IsEquipmentSelected(EEquipmentType::ThermalPlating));
	TestTrue(TEXT("Impact carapace is selected"), Loadout->IsEquipmentSelected(EEquipmentType::ArmorPlating));
	TestEqual(TEXT("Same-cost slot replacement keeps supply stable"), Loadout->GetUsedSupply(), 7);

	TestFalse(TEXT("An over-budget addition is rejected"), Loadout->ToggleEquipment(EEquipmentType::RadiationShield));
	TestFalse(TEXT("Rejected equipment is not selected"), Loadout->IsEquipmentSelected(EEquipmentType::RadiationShield));
	TestTrue(TEXT("Selected armor can be removed"), Loadout->ToggleEquipment(EEquipmentType::ArmorPlating));
	TestTrue(TEXT("Radiation bracers fit after freeing supply"), Loadout->ToggleEquipment(EEquipmentType::RadiationShield));
	TestEqual(TEXT("Revised loadout uses six supply"), Loadout->GetUsedSupply(), 6);

	const FEquipmentStats Stats = Loadout->GetSelectedStats();
	TestEqual(TEXT("Selected bracers contribute radiation resistance"), Stats.RadiationResistance, 40.0f);
	TestEqual(TEXT("Starter pressure seals contribute pressure resistance"), Stats.PressureResistance, 45.0f);
	TestEqual(TEXT("Visor and scrubber dust protection stack"), Stats.DustProtection, 50.0f);
	return true;
}

#endif
