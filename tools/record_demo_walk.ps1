# Records the demo walkthrough as frames, then assembles the video.
#
# Runs Ginnungagap.Smoke.PlayerWalksOutOfCryo under a windowed editor with recording on: PIE in
# its own 1920x1080 window, a fixed 30 Hz game step, one screenshot per frame of the player's own
# view with the HUD, from the opening shot on the sleeper to the title card, with the engine's
# on-screen debug messages (unbuilt reflection captures and the like) turned off first. Then
# tools/assemble_demo_video.py turns Saved/Screenshots/WindowsEditor/Frame_*.png into an MP4 in
# Saved/Video/.
#
# Slow on purpose: a readback every frame holds real time to a few frames a second, which is why
# the walk keeps time by the world clock when recording. Budget twenty to forty minutes.
#
#     powershell -ExecutionPolicy Bypass -File tools/record_demo_walk.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Editor = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$Project = Join-Path $Root "Ginnungagap.uproject"
$Frames = Join-Path $Root "Saved\Screenshots\WindowsEditor"

# Old frames would be stitched in; clear them, keep the named stills.
if (Test-Path $Frames) { Get-ChildItem $Frames -Filter "Frame_*.png" | Remove-Item -Force }

$Args = @(
    "`"$Project`"",
    "-ExecCmds=`"DisableAllScreenMessages; Automation RunTests Ginnungagap.Smoke.PlayerWalksOutOfCryo; Quit`"",
    "-GinnungagapRecordWalk", "-UseFixedTimeStep", "-FPS=30",
    "-unattended", "-nopause", "-TestExit=`"Automation Test Queue Empty`"",
    "-ResX=1920", "-ResY=1080", "-WINDOWED"
)
Write-Host "Recording..."
$Process = Start-Process -FilePath $Editor -ArgumentList $Args -PassThru
$Process.WaitForExit()
$Count = (Get-ChildItem $Frames -Filter "Frame_*.png" -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host "Recorded $Count frames"
if ($Count -gt 0) {
    python (Join-Path $Root "tools\assemble_demo_video.py") --fps 30
}
