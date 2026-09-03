#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Progression/ClassSkillComponent.h"
#include "Progression/ClassSkillTreeSubsystem.h"

/**
 * Runtime half of the payload system: triggering, cooldowns, charges, and the rule that an
 * equipped active contributes nothing until it is actually used.
 *
 * The catalogue tests cover the data; these cover the component that has to hold state correctly
 * while a run is in progress.
 */

namespace
{
	struct FSkillTestRig
	{
		UWorld* World = nullptr;
		AActor* Owner = nullptr;
		UClassSkillComponent* Skills = nullptr;
		UClassSkillTreeSubsystem* Tree = nullptr;
	};

	/**
	 * A component needs an owning actor in a real world, so this builds a throwaway one rather
	 * than using a bare NewObject. Built through UWorld::CreateWorld rather than the editor
	 * automation helper, which would drag the whole UnrealEd module into this module's link.
	 *
	 * The subsystem is constructed against a standalone GameInstance because ClassWithin requires
	 * that outer.
	 *
	 * Every rig must be torn down with DestroyRig. A world created this way is rooted and does not
	 * collect on its own: engine subsystems attach to it -- MassEntitySubsystem among them -- and
	 * hold it alive. Leaked worlds are invisible until something triggers an editor map load, at
	 * which point CheckForWorldGCLeaks turns them into a fatal error and takes the rest of the
	 * automation run down with it.
	 */
	FSkillTestRig MakeRig()
	{
		FSkillTestRig Rig;
		Rig.World = UWorld::CreateWorld(EWorldType::Game, false);
		if (!Rig.World)
		{
			return Rig;
		}

		// A world context is what lets the world be destroyed cleanly again later.
		FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
		Context.SetCurrentWorld(Rig.World);

		Rig.Owner = Rig.World->SpawnActor<AActor>();
		Rig.Skills = NewObject<UClassSkillComponent>(Rig.Owner);
		Rig.Skills->RegisterComponent();

		UGameInstance* TestGameInstance = NewObject<UGameInstance>();
		Rig.Tree = NewObject<UClassSkillTreeSubsystem>(TestGameInstance);
		Rig.Tree->ResetToDefaultSkills();

		return Rig;
	}

	/** Releases the throwaway world. Safe to call on a rig that failed to build. */
	void DestroyRig(FSkillTestRig& Rig)
	{
		if (!Rig.World)
		{
			return;
		}

		GEngine->DestroyWorldContext(Rig.World);
		Rig.World->DestroyWorld(false);
		Rig.World = nullptr;
		Rig.Owner = nullptr;
		Rig.Skills = nullptr;
	}

	/** Destroys the rig however the test leaves, including on an early return. */
	struct FRigGuard
	{
		FSkillTestRig& Rig;
		explicit FRigGuard(FSkillTestRig& InRig) : Rig(InRig) {}
		~FRigGuard() { DestroyRig(Rig); }
	};

	/** Puts the component into a known state without needing saved progression or a subsystem load. */
	void SetupPayload(FSkillTestRig& Rig, const TArray<FString>& Payload, int32 Rank = 1)
	{
		Rig.Skills->SelectedRole = EPressureSuitRole::Scientist;
		for (const FString& SkillID : Payload)
		{
			Rig.Skills->OwnedSkills.SkillRanks.Add(SkillID, Rank);
		}
		Rig.Skills->OwnedSkills.EquippedActiveSkills = Payload;

		// No game instance stands behind a test world, so the catalogue is supplied directly.
		Rig.Skills->SetSkillTree(Rig.Tree);
		Rig.Skills->ResetActivationStateForNewRun();
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSkillActivationRuntimeTest,
	"Ginnungagap.Progression.SkillRuntime.Activation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSkillActivationRuntimeTest::RunTest(const FString& Parameters)
{
	FSkillTestRig Rig = MakeRig();
	FRigGuard Guard(Rig);
	if (!Rig.Skills)
	{
		AddError(TEXT("Could not create a test world for the skill component"));
		return false;
	}

	// Act_EmergencyReseal: 45s duration, 180s cooldown, 2 charges.
	const FString Reseal = TEXT("Act_EmergencyReseal");
	SetupPayload(Rig, {Reseal});
	const FClassSkill Skill = Rig.Tree->GetSkillByID(Reseal);

	// Before triggering, an equipped active is ready and contributing nothing. This is the whole
	// point of the model: bringing a procedure is not the same as using it.
	TestTrue(TEXT("An equipped active starts ready"), Rig.Skills->CanActivateSkill(Reseal));
	TestFalse(TEXT("An untriggered active is not in force"), Rig.Skills->IsSkillActive(Reseal));
	TestEqual(TEXT("An untriggered active contributes nothing"),
		Rig.Skills->GetEffect(SkillEffects::SuitSealIntegrity), 0.0f);
	TestEqual(TEXT("A fresh run starts with full charges"),
		Rig.Skills->GetChargesRemaining(Reseal), Skill.ChargesPerRun);

	// Triggering opens the window and starts the cooldown together.
	TestTrue(TEXT("An equipped, ready active can be triggered"), Rig.Skills->ActivateSkill(Reseal));
	TestTrue(TEXT("Triggering puts the effect in force"), Rig.Skills->IsSkillActive(Reseal));
	TestTrue(TEXT("An active in force contributes its magnitude"),
		Rig.Skills->GetEffect(SkillEffects::SuitSealIntegrity) > 0.0f);
	TestEqual(TEXT("Triggering spends a charge"),
		Rig.Skills->GetChargesRemaining(Reseal), Skill.ChargesPerRun - 1);
	TestEqual(TEXT("The cooldown starts at its full length"),
		Rig.Skills->GetRemainingCooldown(Reseal), Skill.CooldownSeconds);

	// Re-triggering while in force is refused rather than silently burning the second charge.
	TestFalse(TEXT("An active already in force cannot be retriggered"),
		Rig.Skills->CanActivateSkill(Reseal));
	TestFalse(TEXT("A refused retrigger returns false"), Rig.Skills->ActivateSkill(Reseal));
	TestEqual(TEXT("A refused retrigger costs no charge"),
		Rig.Skills->GetChargesRemaining(Reseal), Skill.ChargesPerRun - 1);

	// Run the window out. The cooldown started at activation, so it is still running afterwards --
	// that is what stops an active from behaving like a passive with extra steps.
	Rig.Skills->TickComponent(Skill.DurationSeconds + 1.0f, LEVELTICK_All, nullptr);
	TestFalse(TEXT("The effect lapses when its window closes"), Rig.Skills->IsSkillActive(Reseal));
	TestEqual(TEXT("A lapsed active contributes nothing again"),
		Rig.Skills->GetEffect(SkillEffects::SuitSealIntegrity), 0.0f);
	TestTrue(TEXT("The cooldown outlives the effect window"),
		Rig.Skills->GetRemainingCooldown(Reseal) > 0.0f);
	TestFalse(TEXT("A cooling active cannot be triggered"), Rig.Skills->CanActivateSkill(Reseal));

	// Clear the cooldown and spend the last charge.
	Rig.Skills->TickComponent(Skill.CooldownSeconds, LEVELTICK_All, nullptr);
	TestEqual(TEXT("The cooldown clears to zero, never below"),
		Rig.Skills->GetRemainingCooldown(Reseal), 0.0f);
	TestTrue(TEXT("A cleared active is ready again"), Rig.Skills->CanActivateSkill(Reseal));
	TestTrue(TEXT("The last charge can be spent"), Rig.Skills->ActivateSkill(Reseal));
	TestEqual(TEXT("Spending the last charge empties the count"),
		Rig.Skills->GetChargesRemaining(Reseal), 0);

	// Out of charges is a harder stop than cooldown: waiting no longer helps.
	Rig.Skills->TickComponent(Skill.DurationSeconds + Skill.CooldownSeconds + 1.0f, LEVELTICK_All, nullptr);
	TestEqual(TEXT("Waiting clears the cooldown"), Rig.Skills->GetRemainingCooldown(Reseal), 0.0f);
	TestFalse(TEXT("A spent active cannot be triggered however long you wait"),
		Rig.Skills->CanActivateSkill(Reseal));

	// A new run restores the payload rather than carrying exhaustion across.
	Rig.Skills->ResetActivationStateForNewRun();
	TestEqual(TEXT("A new run restores charges"),
		Rig.Skills->GetChargesRemaining(Reseal), Skill.ChargesPerRun);
	TestTrue(TEXT("A new run leaves the payload ready"), Rig.Skills->CanActivateSkill(Reseal));

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSkillUnlimitedUseTest,
	"Ginnungagap.Progression.SkillRuntime.UnlimitedUse",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSkillUnlimitedUseTest::RunTest(const FString& Parameters)
{
	FSkillTestRig Rig = MakeRig();
	FRigGuard Guard(Rig);
	if (!Rig.Skills)
	{
		AddError(TEXT("Could not create a test world for the skill component"));
		return false;
	}

	// Act_ControlledBreathing: 60s duration, 150s cooldown, no charge limit.
	const FString Breathing = TEXT("Act_ControlledBreathing");
	SetupPayload(Rig, {Breathing});
	const FClassSkill Skill = Rig.Tree->GetSkillByID(Breathing);

	// -1 rather than a count, so a HUD can tell "unlimited" from "plenty left" without knowing
	// the catalogue.
	TestEqual(TEXT("A cooldown-only active reports unlimited charges"),
		Rig.Skills->GetChargesRemaining(Breathing), -1);

	// Cycle it more times than any charge count would allow, to prove nothing is being decremented.
	for (int32 Cycle = 0; Cycle < 5; ++Cycle)
	{
		TestTrue(TEXT("A cooldown-only active can be triggered again each cycle"),
			Rig.Skills->ActivateSkill(Breathing));
		Rig.Skills->TickComponent(Skill.DurationSeconds + Skill.CooldownSeconds + 1.0f,
			LEVELTICK_All, nullptr);
	}

	TestEqual(TEXT("Repeated use never consumes a charge"),
		Rig.Skills->GetChargesRemaining(Breathing), -1);

	// Unequipping takes the runtime state with it, so an active cannot be swapped out and back in
	// to escape its own cooldown.
	TestTrue(TEXT("The active triggers once more"), Rig.Skills->ActivateSkill(Breathing));
	TestTrue(TEXT("It is now cooling"), Rig.Skills->GetRemainingCooldown(Breathing) > 0.0f);
	TestTrue(TEXT("It can be unequipped"), Rig.Skills->UnequipActiveSkill(Breathing));
	TestFalse(TEXT("An unequipped active is no longer in force"),
		Rig.Skills->IsSkillActive(Breathing));
	TestEqual(TEXT("An unequipped active contributes nothing"),
		Rig.Skills->GetEffect(SkillEffects::OxygenConsumption), 0.0f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSkillSlotAddressingTest,
	"Ginnungagap.Progression.SkillRuntime.SlotAddressing",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSkillSlotAddressingTest::RunTest(const FString& Parameters)
{
	FSkillTestRig Rig = MakeRig();
	FRigGuard Guard(Rig);
	if (!Rig.Skills)
	{
		AddError(TEXT("Could not create a test world for the skill component"));
		return false;
	}

	SetupPayload(Rig, {TEXT("Act_EmergencyReseal"), TEXT("Act_ControlledBreathing")});

	// Slots address the payload in order, which is what the ability-bar keys rely on.
	TestEqual(TEXT("Slot zero is the first equipped skill"),
		Rig.Skills->GetSkillInSlot(0), TEXT("Act_EmergencyReseal"));
	TestEqual(TEXT("Slot one is the second equipped skill"),
		Rig.Skills->GetSkillInSlot(1), TEXT("Act_ControlledBreathing"));

	// Out-of-range and negative indices must be answered, not crash: input can ask for any slot.
	TestTrue(TEXT("An unfilled slot is empty"), Rig.Skills->GetSkillInSlot(2).IsEmpty());
	TestTrue(TEXT("A negative slot is empty"), Rig.Skills->GetSkillInSlot(-1).IsEmpty());
	TestTrue(TEXT("A slot past the payload is empty"), Rig.Skills->GetSkillInSlot(99).IsEmpty());

	// Triggering an empty slot is a no-op rather than an error.
	TestFalse(TEXT("Activating an empty slot fails quietly"), Rig.Skills->ActivateSkillSlot(2));
	TestFalse(TEXT("Activating a negative slot fails quietly"), Rig.Skills->ActivateSkillSlot(-1));

	TestEqual(TEXT("Free slots account for what is equipped"), Rig.Skills->GetFreeActiveSlots(),
		FClassProgression::MaxEquippedActiveSkills - 2);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSkillChargeAccountingTest,
	"Ginnungagap.Progression.SkillRuntime.ChargeAccounting",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSkillChargeAccountingTest::RunTest(const FString& Parameters)
{
	UGameInstance* TestGameInstance = NewObject<UGameInstance>();
	UClassSkillTreeSubsystem* Tree = NewObject<UClassSkillTreeSubsystem>(TestGameInstance);
	Tree->ResetToDefaultSkills();

	// Charge-limited and cooldown-only actives must both exist, or "limited uses" is a claim the
	// catalogue does not honour and every active plays the same way.
	int32 ChargeLimited = 0;
	int32 CooldownOnly = 0;
	for (const FClassSkill& Skill : Tree->GetAllSkillsForRole(EPressureSuitRole::Scientist))
	{
		if (Skill.Activation != ESkillActivation::Active)
		{
			continue;
		}

		if (Skill.ChargesPerRun > 0)
		{
			++ChargeLimited;

			// A single-charge active would be indistinguishable from a one-shot and makes the
			// cooldown meaningless, so charged actives carry at least two.
			TestTrue(TEXT("A charge-limited active has more than one use"), Skill.ChargesPerRun >= 2);
		}
		else
		{
			++CooldownOnly;
		}
	}

	TestTrue(TEXT("Some actives are charge-limited"), ChargeLimited > 0);
	TestTrue(TEXT("Some actives are limited only by cooldown"), CooldownOnly > 0);

	return true;
}

#endif
