#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Engine/Engine.h"
#include "Engine/World.h"

#include "CoopSurvivalCharacter.h"
#include "Equipment/EquipmentComponent.h"
#include "Inventory/InventoryComponent.h"
#include "Inventory/ItemDefinition.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"

/**
 * The field supply catalogue, as authored rather than as intended.
 *
 * These load the real data assets instead of building definitions in code. That is the whole point:
 * the consumable fields on UItemDefinition were already covered by the unit tests, and what was
 * never covered was whether any asset actually sets them correctly. A definition with the right
 * code behind it and a zero in the field is indistinguishable from a missing feature at runtime,
 * and it is exactly the mistake a scripted authoring pass makes quietly.
 *
 * The equipment repair path needs a real pawn -- CanUseItem reaches for a component on the
 * character -- so it lives here rather than with the component tests.
 */

namespace FieldSupplyPie
{
	const TCHAR* ItemPath = TEXT("/Game/Assets/Gameplay/FieldSupplies/Data/Items/");

	UWorld* FindPieWorld()
	{
		if (!GEngine)
		{
			return nullptr;
		}

		for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			if (Context.WorldType == EWorldType::PIE && Context.World())
			{
				return Context.World();
			}
		}
		return nullptr;
	}

	UItemDefinition* Load(const FString& Id)
	{
		return LoadObject<UItemDefinition>(nullptr, *(FString(ItemPath) + TEXT("DA_Item_") + Id));
	}

	/** A worn helmet at a known fraction of its durability, so repair has something to bite on. */
	FEquipmentItem WornHelmet(float Durability)
	{
		FEquipmentItem Item;
		Item.Slot = EEquipmentSlot::Head;
		Item.DisplayName = TEXT("Test Helmet");
		Item.MaxDurability = 100.0f;
		Item.CurrentDurability = Durability;
		return Item;
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertFieldSupplies, FAutomationTestBase*, Test);

bool FAssertFieldSupplies::Update()
{
	UWorld* World = FieldSupplyPie::FindPieWorld();
	if (!World)
	{
		Test->AddError(TEXT("No PIE world for the field supply assertions"));
		return true;
	}

	// --- Every authored definition exists and is actually consumable ---------------------------
	// A catalogue entry that is not consumable can never be used, and nothing else in the game
	// would ever tell you.
	const TArray<FString> Expected = {
		TEXT("EmergencyOxygenCartridge"), TEXT("SuitPatchSealant"), TEXT("FieldRepairKit"),
		TEXT("TraumaKit"), TEXT("CompoundSplint"), TEXT("GeneralMedicalAmpoule"),
		TEXT("ChelationInjector"), TEXT("RecompressionAmpoule"),
		TEXT("ThermalRegulationWrap"), TEXT("CoolantGelPack")
	};

	for (const FString& Id : Expected)
	{
		UItemDefinition* Item = FieldSupplyPie::Load(Id);
		if (!Item)
		{
			Test->AddError(FString::Printf(TEXT("Field supply %s was not authored"), *Id));
			continue;
		}

		Test->TestTrue(FString::Printf(TEXT("%s is consumable"), *Id), Item->bIsConsumable);
		Test->TestTrue(FString::Printf(TEXT("%s has a mesh to appear as in the world"), *Id),
			Item->WorldMesh != nullptr);

		// The one that matters: an entry setting none of the effect fields does nothing at all when
		// used, which is the failure this whole file exists to catch.
		const bool bDoesSomething = Item->OxygenRestorePercent > 0.0f
			|| Item->HealthRestorePercent > 0.0f
			|| Item->SuitIntegrityRestore > 0.0f
			|| Item->EquipmentRepairAmount > 0.0f
			|| Item->TreatmentStrength > 0.0f;
		Test->TestTrue(FString::Printf(TEXT("%s has at least one live effect"), *Id), bDoesSomething);

		// Supplies are meant to be shared out. One that cannot be handed over is a bug in the data
		// rather than a design choice, since none of these are mission critical.
		Test->TestTrue(FString::Printf(TEXT("%s can be dropped for a crewmate"), *Id), Item->bCanDrop);
		Test->TestFalse(FString::Printf(TEXT("%s is not a mission item"), *Id), Item->bMissionItem);
	}

	// --- A targeted treatment names its affliction ----------------------------------------------
	// Setting a strength but forgetting the flag silently turns a targeted item into a general one,
	// which is the single easiest mistake to make in this data and impossible to see in the editor.
	if (UItemDefinition* Chelation = FieldSupplyPie::Load(TEXT("ChelationInjector")))
	{
		Test->TestTrue(TEXT("The chelation injector treats a specific affliction"),
			Chelation->bTreatsSpecificEffect);
		Test->TestEqual(TEXT("The chelation injector treats radiation sickness"),
			Chelation->TreatedEffect, EPlayerStatusEffect::RadiationSickness);
	}

	if (UItemDefinition* General = FieldSupplyPie::Load(TEXT("GeneralMedicalAmpoule")))
	{
		Test->TestFalse(TEXT("The general ampoule is deliberately untargeted"),
			General->bTreatsSpecificEffect);
		Test->TestTrue(TEXT("The general ampoule still treats something"),
			General->TreatmentStrength > 0.0f);
	}

	// --- The repair kit, on a real pawn ---------------------------------------------------------
	UItemDefinition* Kit = FieldSupplyPie::Load(TEXT("FieldRepairKit"));
	Test->TestNotNull(TEXT("The field repair kit was authored"), Kit);

	if (Kit)
	{
		Test->TestTrue(TEXT("The field repair kit restores equipment durability"),
			Kit->EquipmentRepairAmount > 0.0f);

		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		ACoopSurvivalCharacter* Crew = World->SpawnActor<ACoopSurvivalCharacter>(
			ACoopSurvivalCharacter::StaticClass(), FTransform(FVector(0, 0, 200)), Params);
		Test->TestNotNull(TEXT("Spawned a crew member to mend gear on"), Crew);

		UInventoryComponent* Inventory = Crew ? Crew->FindComponentByClass<UInventoryComponent>() : nullptr;
		UEquipmentComponent* Equipment = Crew ? Crew->FindComponentByClass<UEquipmentComponent>() : nullptr;

		if (Inventory && Equipment)
		{
			Inventory->AddItem(Kit, 1);

			// Nothing worn yet. Using a kit here would spend it on nothing, which is the same trap
			// the medkit-at-full-health rule exists to avoid.
			Test->TestFalse(TEXT("A repair kit is refused when nothing is worn"),
				Inventory->CanUseItem(Kit));

			Equipment->EquipItem(FieldSupplyPie::WornHelmet(100.0f));
			Test->TestFalse(TEXT("A repair kit is refused when the worn gear is whole"),
				Inventory->CanUseItem(Kit));

			Equipment->EquipItem(FieldSupplyPie::WornHelmet(40.0f));
			Test->TestTrue(TEXT("A repair kit is offered once gear is damaged"),
				Inventory->CanUseItem(Kit));

			const float Before = Equipment->GetSlotCondition(EEquipmentSlot::Head);
			const bool bUsed = Inventory->UseItem(Kit);
			Test->TestTrue(TEXT("Using a repair kit on damaged gear succeeds"), bUsed);

			if (bUsed)
			{
				Test->TestTrue(TEXT("Using a repair kit restores condition"),
					Equipment->GetSlotCondition(EEquipmentSlot::Head) > Before);

				// A carried kit must not be a bench in a pocket. Whatever the tuning, one use
				// cannot be a full restore or there is no reason to walk back to the workshop.
				Test->TestTrue(TEXT("One kit does not fully restore worn gear"),
					Equipment->GetSlotCondition(EEquipmentSlot::Head) < 1.0f);

				// Consumed, not merely applied.
				Test->TestEqual(TEXT("A used repair kit is spent"),
					Inventory->GetItemQuantity(Kit), 0);
				Test->TestFalse(TEXT("A spent repair kit cannot be used again"),
					Inventory->CanUseItem(Kit));
			}
		}
		else if (Crew)
		{
			Test->AddError(TEXT("The crew member has no inventory or equipment component"));
		}

		if (Crew)
		{
			Crew->Destroy();
		}
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapFieldSupplyPieTest,
	"Ginnungagap.Smoke.FieldSupplies",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapFieldSupplyPieTest::RunTest(const FString& Parameters)
{
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertFieldSupplies(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
