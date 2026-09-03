#include "Animation/MetaHumanCopyPoseAnimInstance.h"

void FMetaHumanCopyPoseAnimInstanceProxy::Initialize(UAnimInstance* Instance)
{
    FAnimInstanceProxy::Initialize(Instance);
    FAnimationInitializeContext Context(this);
    CopyPoseFromMesh.bUseAttachedParent = true;
    CopyPoseFromMesh.bCopyCurves = true;
    CopyPoseFromMesh.bCopyCustomAttributes = true;
    CopyPoseFromMesh.Initialize_AnyThread(Context);
}

void FMetaHumanCopyPoseAnimInstanceProxy::PreUpdate(UAnimInstance* Instance, float DeltaSeconds)
{
    FAnimInstanceProxy::PreUpdate(Instance, DeltaSeconds);
    CopyPoseFromMesh.PreUpdate(Instance);
}

void FMetaHumanCopyPoseAnimInstanceProxy::UpdateAnimationNode(const FAnimationUpdateContext& Context)
{
    UpdateCounter.Increment();
    CopyPoseFromMesh.Update_AnyThread(Context);
}

bool FMetaHumanCopyPoseAnimInstanceProxy::Evaluate(FPoseContext& Output)
{
    CopyPoseFromMesh.Evaluate_AnyThread(Output);
    return true;
}

UMetaHumanCopyPoseAnimInstance::UMetaHumanCopyPoseAnimInstance()
{
    bUseMultiThreadedAnimationUpdate = false;
}

FAnimInstanceProxy* UMetaHumanCopyPoseAnimInstance::CreateAnimInstanceProxy()
{
    return new FMetaHumanCopyPoseAnimInstanceProxy(this);
}
