param(
    [string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.8"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ProjectFile = Join-Path $ProjectRoot "Ginnungagap.uproject"
$EditorCmd = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$CookLog = Join-Path $ProjectRoot "Saved\Logs\CryoRoomCook.log"

if (-not (Test-Path -LiteralPath $EditorCmd)) {
    throw "UnrealEditor-Cmd.exe was not found under $EngineRoot"
}

& $EditorCmd $ProjectFile `
    -run=cook `
    -targetplatform=Windows `
    "-Map=/Game/Assets/Maps/ShipProduction/L_CryoRoom_Review" `
    -CookCultures=en `
    -unversioned `
    -unattended `
    -nop4 `
    -noxgeshadercompile `
    "-abslog=$CookLog"

if ($LASTEXITCODE -ne 0) {
    throw "CRYO-01 review-map cook failed with exit code $LASTEXITCODE. See $CookLog"
}

Write-Host "CRYO-01 review-map cook succeeded. Log: $CookLog"
