param(
    [string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.8"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ProjectFile = Join-Path $ProjectRoot "Ginnungagap.uproject"
$EditorCmd = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$CookLog = Join-Path $ProjectRoot "Saved\Logs\ShipDistrictCook.log"

if (-not (Test-Path -LiteralPath $EditorCmd)) {
    throw "UnrealEditor-Cmd.exe was not found under $EngineRoot"
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

& $EditorCmd $ProjectFile `
    -run=cook `
    -targetplatform=Windows `
    "-Map=$PlayableMaps" `
    -CookCultures=en `
    -unversioned `
    -unattended `
    -nop4 `
    -noxgeshadercompile `
    "-abslog=$CookLog"

if ($LASTEXITCODE -ne 0) {
    throw "Ship district cook failed with exit code $LASTEXITCODE. See $CookLog"
}

Write-Host "Ship district cook succeeded. Log: $CookLog"
