# Packages the corvette as a standalone Windows game: main menu plus L_Corvette_ThrustStack,
# Development configuration, archived under Builds\Corvette-Windows-<Configuration>\Windows.
#
#     powershell -ExecutionPolicy Bypass -File tools/package_corvette.ps1 [-Configuration Shipping]
#
# Run it alone: the cook loads every asset the maps reference and a parallel editor or build
# fights it for the DLLs and the DDC. Budget thirty to sixty minutes the first time.
#
# Known: the cook commandlet has hung at shutdown after "Cook by the book total time". If the
# log stops there and UnrealEditor-Cmd.exe is still alive, kill it and rerun with
# -skipbuild -skipcook (the cooked data is complete); this script does that with -StageOnly.
param(
    [ValidateSet("Development", "Shipping")]
    [string]$Configuration = "Development",
    [switch]$StageOnly,
    [string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.8",
    [string]$ArchiveDirectory = ""
)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ProjectFile = Join-Path $ProjectRoot "Ginnungagap.uproject"
$RunUAT = Join-Path $EngineRoot "Engine\Build\BatchFiles\RunUAT.bat"
$StagingDirectory = Join-Path ([IO.Path]::GetTempPath()) "Ginnungagap\CorvetteStage-$Configuration"
if ([string]::IsNullOrWhiteSpace($ArchiveDirectory)) {
    $ArchiveDirectory = Join-Path $ProjectRoot "Builds\Corvette-Windows-$Configuration"
}
if (-not (Test-Path -LiteralPath $RunUAT)) { throw "RunUAT.bat was not found under $EngineRoot" }
$Maps = @(
    "/Game/UI/MainMenu",
    "/Game/Assets/Maps/ShipProduction/L_Corvette_ThrustStack"
) -join "+"
$Steps = if ($StageOnly) { @("-skipbuild", "-skipcook") } else { @("-build", "-cook") }
& $RunUAT BuildCookRun `
    "-project=$ProjectFile" `
    -target=Ginnungagap `
    -noP4 `
    -utf8output `
    -unattended `
    -platform=Win64 `
    "-clientconfig=$Configuration" `
    @Steps `
    "-map=$Maps" `
    -CookCultures=en `
    -stage `
    "-stagingdirectory=$StagingDirectory" `
    -pak `
    -archive `
    "-archivedirectory=$ArchiveDirectory"
if ($LASTEXITCODE -ne 0) { throw "BuildCookRun failed with exit code $LASTEXITCODE" }
Write-Host "Packaged to $ArchiveDirectory"
