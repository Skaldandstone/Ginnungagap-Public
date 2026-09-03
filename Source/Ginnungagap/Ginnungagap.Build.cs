using UnrealBuildTool;
using System.Collections.Generic;
public class Ginnungagap : ModuleRules
{
    public Ginnungagap(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicIncludePaths.AddRange(new string[] { ModuleDirectory });

        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "AIModule", "NavigationSystem", "GameplayTasks", "GameplayStateTreeModule", "StateTreeModule", "UMG", "PCG", "Niagara", "AnimGraphRuntime" });

        // Microphone-driven noise for the stealth system. AudioCaptureCore owns the device
        // interface; the platform backends ship with the engine's AudioCapture plugin.
        PrivateDependencyModuleNames.Add("AudioCaptureCore");

        PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore", "OnlineSubsystem", "OnlineSubsystemUtils" });

        // The Perlin-noise camera shake pattern (the Bloom hulk's roar) lives in the EngineCameras
        // plugin, not Engine. It is an engine plugin enabled by default.
        PrivateDependencyModuleNames.Add("EngineCameras");

        // PIE automation. The latent commands that start and stop a play session
        // (FStartPIECommand, FEndPlayMapCommand) are implemented in UnrealEd, not Engine, so a
        // test that actually plays the map cannot be written without it. Guarded on bBuildEditor
        // so no shipping target ever links the editor.
        if (Target.bBuildEditor)
        {
            PrivateDependencyModuleNames.Add("UnrealEd");
        }
    }
}
