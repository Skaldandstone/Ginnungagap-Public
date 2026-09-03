#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "CoopSurvivalCharacter.h"
#include "Meta/CharacterProfile.h"
#include "Bloom/PathogenLoadComponent.h"
#include "Materials/MaterialInterface.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/Actor.h"
#include "UObject/UnrealType.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPlayerSuitReplicationContractTest,
    "Ginnungagap.Multiplayer.PlayerSuit.ReplicationContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FPlayerSuitReplicationContractTest::RunTest(const FString& Parameters)
{
    FProperty* SuitRole = FindFProperty<FProperty>(
        ACoopSurvivalCharacter::StaticClass(), GET_MEMBER_NAME_CHECKED(ACoopSurvivalCharacter, PressureSuitRole));
    TestNotNull(TEXT("PressureSuitRole property exists"), SuitRole);
    if (SuitRole)
    {
        TestTrue(TEXT("PressureSuitRole is replicated"), SuitRole->HasAnyPropertyFlags(CPF_Net));
        TestEqual(TEXT("PressureSuitRole refreshes visuals through its RepNotify"), SuitRole->RepNotifyFunc,
            GET_FUNCTION_NAME_CHECKED(ACoopSurvivalCharacter, OnRep_PressureSuitRole));
    }

    FProperty* OversuitEquipped = FindFProperty<FProperty>(
        ACoopSurvivalCharacter::StaticClass(), GET_MEMBER_NAME_CHECKED(ACoopSurvivalCharacter, bPressureOversuitEquipped));
    TestNotNull(TEXT("Pressure oversuit state exists"), OversuitEquipped);
    if (OversuitEquipped)
    {
        TestTrue(TEXT("Pressure oversuit state is replicated"), OversuitEquipped->HasAnyPropertyFlags(CPF_Net));
        TestEqual(TEXT("Pressure oversuit state refreshes isolated rigid layers"), OversuitEquipped->RepNotifyFunc,
            GET_FUNCTION_NAME_CHECKED(ACoopSurvivalCharacter, OnRep_PressureOversuitEquipped));
    }

    FProperty* MetaHumanClass = FindFProperty<FProperty>(
        ACoopSurvivalCharacter::StaticClass(), GET_MEMBER_NAME_CHECKED(ACoopSurvivalCharacter, MetaHumanCharacterClass));
    TestNotNull(TEXT("Swappable MetaHuman class exists"), MetaHumanClass);
    if (MetaHumanClass)
    {
        TestTrue(TEXT("MetaHuman class selection is replicated"), MetaHumanClass->HasAnyPropertyFlags(CPF_Net));
        TestEqual(TEXT("MetaHuman class selection rebuilds the character layer"), MetaHumanClass->RepNotifyFunc,
            GET_FUNCTION_NAME_CHECKED(ACoopSurvivalCharacter, OnRep_MetaHumanCharacterClass));
    }

    FProperty* InfectionState = FindFProperty<FProperty>(
        UPathogenLoadComponent::StaticClass(), GET_MEMBER_NAME_CHECKED(UPathogenLoadComponent, InfectionState));
    FProperty* PathogenLoad = FindFProperty<FProperty>(
        UPathogenLoadComponent::StaticClass(), GET_MEMBER_NAME_CHECKED(UPathogenLoadComponent, PathogenLoad));
    TestTrue(TEXT("Infection state replicates"), InfectionState && InfectionState->HasAnyPropertyFlags(CPF_Net));
    TestTrue(TEXT("Pathogen load replicates"), PathogenLoad && PathogenLoad->HasAnyPropertyFlags(CPF_Net));

    const EPressureSuitRole Roles[] = {
        EPressureSuitRole::Scientist, EPressureSuitRole::Engineering,
        EPressureSuitRole::Medical, EPressureSuitRole::Security
    };
    for (const EPressureSuitRole Role : Roles)
    {
        FCharacterProfile Profile;
        Profile.SuitRole = Role;
        TestEqual(TEXT("Profile retains selected suit role"), Profile.SuitRole, Role);
    }
    const FCharacterProfile DefaultProfile;
    TestEqual(TEXT("Existing saves and new profiles default to the first assembled MetaHuman"),
        DefaultProfile.MetaHumanPresetId, FName(TEXT("PlayerFace01")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPlayerSuitNetworkAssetResolutionTest,
    "Ginnungagap.Multiplayer.PlayerSuit.NetworkAssetResolution",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FPlayerSuitNetworkAssetResolutionTest::RunTest(const FString& Parameters)
{
    USkeletalMesh* CryoBodysuit = LoadObject<USkeletalMesh>(nullptr,
        TEXT("/Game/Characters/Player/Undersuit/CryoBodysuitV32/SK_CryoBodysuit_V32_Manny.SK_CryoBodysuit_V32_Manny"));
    USkeletalMesh* Manny = LoadObject<USkeletalMesh>(nullptr,
        TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"));
    USkeletalMesh* FittedCryoBodysuit = LoadObject<USkeletalMesh>(nullptr,
        TEXT("/Game/Characters/Player/Undersuit/CryoBodysuitV34/SK_CryoBodysuit_V34_Face01.SK_CryoBodysuit_V34_Face01"));
    USkeletalMesh* MetaHumanBody = LoadObject<USkeletalMesh>(nullptr,
        TEXT("/Game/Characters/MetaHumans/Assembled/PlayerFace01/Body/SKM_MHC_Face01_Ada_BodyMesh.SKM_MHC_Face01_Ada_BodyMesh"));
    TestNotNull(TEXT("Authored V32 cryo bodysuit resolves"), CryoBodysuit);
    TestNotNull(TEXT("Manny animation driver resolves"), Manny);
    if (CryoBodysuit && Manny)
    {
        TestEqual(TEXT("V32 garment uses the exact Manny skeleton for Leader Pose"),
            CryoBodysuit->GetSkeleton(), Manny->GetSkeleton());
    }
    TestNotNull(TEXT("Continuous V34 fitted cryo bodysuit resolves"), FittedCryoBodysuit);
    TestNotNull(TEXT("PlayerFace01 MetaHuman body driver resolves"), MetaHumanBody);
    if (FittedCryoBodysuit && MetaHumanBody)
    {
        TestEqual(TEXT("V34 garment uses the exact PlayerFace01 body skeleton for Leader Pose"),
            FittedCryoBodysuit->GetSkeleton(), MetaHumanBody->GetSkeleton());
    }
    TestNotNull(TEXT("Default assembled MetaHuman class resolves"), LoadClass<AActor>(nullptr,
        TEXT("/Game/Characters/MetaHumans/Assembled/PlayerFace01/BP_PlayerFace01.BP_PlayerFace01_C")));

    const TCHAR* RoleMaterials[] = {
        TEXT("/Game/Characters/Player/Suit/Materials/MI_Suit_Crew.MI_Suit_Crew"),
        TEXT("/Game/Characters/Player/Suit/Materials/MI_Suit_Engineering.MI_Suit_Engineering"),
        TEXT("/Game/Characters/Player/Suit/Materials/MI_Suit_Medical.MI_Suit_Medical"),
        TEXT("/Game/Characters/Player/Suit/Materials/MI_Suit_Security.MI_Suit_Security")
    };
    const TCHAR* RoleModules[] = {
        TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_Module_Crew.SM_Suit_Module_Crew"),
        TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_Module_Engineering.SM_Suit_Module_Engineering"),
        TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_Module_Medical.SM_Suit_Module_Medical"),
        TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_Module_Security.SM_Suit_Module_Security")
    };
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(RoleMaterials); ++Index)
    {
        TestNotNull(TEXT("Replicated role material resolves"), LoadObject<UMaterialInterface>(nullptr, RoleMaterials[Index]));
        TestNotNull(TEXT("Replicated role module resolves"), LoadObject<UStaticMesh>(nullptr, RoleModules[Index]));
    }
    return true;
}

#endif
