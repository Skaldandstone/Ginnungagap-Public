#pragma once

#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "AnimNodes/AnimNode_CopyPoseFromMesh.h"
#include "MetaHumanCopyPoseAnimInstance.generated.h"

USTRUCT()
struct GINNUNGAGAP_API FMetaHumanCopyPoseAnimInstanceProxy : public FAnimInstanceProxy
{
    GENERATED_BODY()

    FMetaHumanCopyPoseAnimInstanceProxy() = default;
    explicit FMetaHumanCopyPoseAnimInstanceProxy(UAnimInstance* Instance)
        : FAnimInstanceProxy(Instance)
    {
    }

    virtual void Initialize(UAnimInstance* Instance) override;
    virtual void PreUpdate(UAnimInstance* Instance, float DeltaSeconds) override;
    virtual void UpdateAnimationNode(const FAnimationUpdateContext& Context) override;
    virtual bool Evaluate(FPoseContext& Output) override;

private:
    FAnimNode_CopyPoseFromMesh CopyPoseFromMesh;
};

/**
 * Copies animation by bone name from the first attached parent skeletal mesh.
 * This safely bridges the compact gameplay driver to MetaHuman's corrective-bone skeleton.
 */
UCLASS(Transient, NotBlueprintable)
class GINNUNGAGAP_API UMetaHumanCopyPoseAnimInstance : public UAnimInstance
{
    GENERATED_BODY()

public:
    UMetaHumanCopyPoseAnimInstance();
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
};
