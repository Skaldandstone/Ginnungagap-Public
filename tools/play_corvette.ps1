# Plays the corvette. Launches the editor as a game, windowed 1920x1080, straight into
# L_Corvette_ThrustStack with no menu in the way: the crew wakes in the casualty station's pod,
# suits up, and works the objective chain down to the power deck and up to the CIC.
#
#     powershell -ExecutionPolicy Bypass -File tools/play_corvette.ps1
#
# Add -Menu to start at the main menu instead (its Play modes also open the corvette).
param([switch]$Menu)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Editor = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$Project = Join-Path $Root "Ginnungagap.uproject"
$Map = if ($Menu) { "/Game/UI/MainMenu" } else { "/Game/Assets/Maps/ShipProduction/L_Corvette_ThrustStack" }
& $Editor "`"$Project`"" $Map -game -WINDOWED -ResX=1920 -ResY=1080 -log
