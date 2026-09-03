param(
    [ValidateSet("Development", "Shipping")]
    [string]$Configuration = "Development",
    [string]$PackageDirectory = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($PackageDirectory)) {
    $PackageDirectory = Join-Path $ProjectRoot "Builds\ShipDistricts-Windows-$Configuration"
}

$Executable = Get-ChildItem -LiteralPath $PackageDirectory -Recurse -Filter "Ginnungagap.exe" |
    Select-Object -First 1
if (-not $Executable) {
    throw "Ginnungagap.exe was not found under $PackageDirectory"
}

$LogDirectory = Join-Path $PackageDirectory "SmokeLogs"
New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
$ShipMaps = @(
    "L_Small_Companionway_Showcase",
    "L_Medium_ExpressSpine_Showcase",
    "L_Large_CarrierConcourse_Showcase"
)

$DefaultLogPath = Join-Path $LogDirectory "DefaultStartup.log"
$DefaultProcess = Start-Process `
    -FilePath $Executable.FullName `
    -ArgumentList @("-nullrhi", "-unattended", "-nosplash", "-ExecCmds=Quit", "-abslog=$DefaultLogPath") `
    -WindowStyle Hidden `
    -Wait `
    -PassThru
if ($DefaultProcess.ExitCode -ne 0) {
    throw "Default startup exited with code $($DefaultProcess.ExitCode). See $DefaultLogPath"
}
$DefaultLogText = Get-Content -LiteralPath $DefaultLogPath -Raw
if ($DefaultLogText -notmatch "Load map complete /Game/UI/MainMenu") {
    throw "Default startup did not load the main menu. See $DefaultLogPath"
}
Write-Host "Passed: default startup map"

foreach ($MapName in $ShipMaps) {
    $MapPath = "/Game/Assets/Maps/ShipProduction/$MapName"
    $LogPath = Join-Path $LogDirectory "$MapName.log"
    $Process = Start-Process `
        -FilePath $Executable.FullName `
        -ArgumentList @($MapPath, "-nullrhi", "-unattended", "-nosplash", "-ExecCmds=Quit", "-abslog=$LogPath") `
        -WindowStyle Hidden `
        -Wait `
        -PassThru

    if ($Process.ExitCode -ne 0) {
        throw "$MapName exited with code $($Process.ExitCode). See $LogPath"
    }
    $LogText = Get-Content -LiteralPath $LogPath -Raw
    if ($LogText -notmatch "Load map complete /Game/Assets/Maps/ShipProduction/$MapName") {
        throw "$MapName exited without confirming map load. See $LogPath"
    }
    if ($LogText -match "Log[^\r\n]*: (Error|Fatal):") {
        throw "$MapName logged a runtime error. See $LogPath"
    }
    Write-Host "Passed: $MapName"
}

Write-Host "All packaged ship districts passed. Logs: $LogDirectory"
