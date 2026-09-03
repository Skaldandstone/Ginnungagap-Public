param(
    [ValidateSet("Development", "Shipping")]
    [string]$Configuration = "Development",
    [string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.8",
    [string]$ArchiveDirectory = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ProjectFile = Join-Path $ProjectRoot "Ginnungagap.uproject"
$RunUAT = Join-Path $EngineRoot "Engine\Build\BatchFiles\RunUAT.bat"
$StagingDirectory = Join-Path ([IO.Path]::GetTempPath()) "Ginnungagap\PlayablePackageStage-$Configuration"

if ([string]::IsNullOrWhiteSpace($ArchiveDirectory)) {
    $ArchiveDirectory = Join-Path $ProjectRoot "Builds\ShipDistricts-Windows-$Configuration"
}

if (-not (Test-Path -LiteralPath $RunUAT)) {
    throw "RunUAT.bat was not found under $EngineRoot"
}
if (-not (Test-Path -LiteralPath $ProjectFile)) {
    throw "Ginnungagap.uproject was not found under $ProjectRoot"
}

$PlayableMaps = @(
    "/Game/UI/MainMenu",
    "/Game/Assets/Maps/ShipProduction/L_Small_Companionway_Showcase",
    "/Game/Assets/Maps/ShipProduction/L_Medium_ExpressSpine_Showcase",
    "/Game/Assets/Maps/ShipProduction/L_Large_CarrierConcourse_Showcase"
) -join "+"

& $RunUAT BuildCookRun `
    "-project=$ProjectFile" `
    -target=Ginnungagap `
    -noP4 `
    -utf8output `
    -unattended `
    -platform=Win64 `
    "-clientconfig=$Configuration" `
    -build `
    -cook `
    "-map=$PlayableMaps" `
    -CookCultures=en `
    -stage `
    "-stagingdirectory=$StagingDirectory" `
    -pak `
    -iostore `
    -compressed `
    -archive `
    "-archivedirectory=$ArchiveDirectory" `
    -noxgeshadercompile

if ($LASTEXITCODE -ne 0) {
    throw "Windows package failed with exit code $LASTEXITCODE"
}

$Executable = Get-ChildItem -LiteralPath $ArchiveDirectory -Recurse -Filter "Ginnungagap.exe" |
    Select-Object -First 1
if (-not $Executable) {
    throw "Packaging reported success but Ginnungagap.exe was not found under $ArchiveDirectory"
}

Write-Host "Ship district package succeeded: $($Executable.FullName)"
