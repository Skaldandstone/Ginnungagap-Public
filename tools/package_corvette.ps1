# Packages the corvette as a standalone Windows game: main menu plus L_Corvette_ThrustStack,
# Development configuration, archived under Builds\Corvette-Windows-<Configuration>\Windows.
#
#     powershell -ExecutionPolicy Bypass -File tools/package_corvette.ps1 [-Configuration Shipping]
#
# Run it alone: the cook loads every asset the maps reference and a parallel editor or build
# fights it for the DLLs and the DDC. Budget thirty to sixty minutes the first time.
#
# The cook commandlet hangs at shutdown now and then, after "LogCook: Display: Done!": the cooked
# data is complete but UnrealEditor-Cmd.exe never exits, and once it sat that way for twelve hours.
# This script watches for that: three minutes after Done with the commandlet still alive, it is
# killed and the stage step is rerun with -skipbuild -skipcook. -StageOnly runs only that step.
param(
    [ValidateSet("Development", "Shipping")]
    [string]$Configuration = "Development",
    [switch]$StageOnly,
    [string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.8",
    [string]$ArchiveDirectory = "",
    [int]$CookHangSeconds = 180
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
$LogDir = Join-Path $ProjectRoot "Saved\Logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Invoke-BuildCookRun([string[]]$Steps, [string]$LogName) {
    $UatLog = Join-Path $LogDir $LogName
    if (Test-Path -LiteralPath $UatLog) { Remove-Item -LiteralPath $UatLog -Force }
    $Args = @("BuildCookRun", "-project=`"$ProjectFile`"", "-target=Ginnungagap", "-noP4", "-utf8output", "-unattended",
        "-platform=Win64", "-clientconfig=$Configuration") + $Steps + @("-map=$Maps", "-CookCultures=en", "-stage",
        "-stagingdirectory=`"$StagingDirectory`"", "-pak", "-archive", "-archivedirectory=`"$ArchiveDirectory`"")
    $Proc = Start-Process -FilePath $RunUAT -ArgumentList $Args -NoNewWindow -PassThru -RedirectStandardOutput $UatLog
    # Touching the handle makes PowerShell keep the process object, so ExitCode is filled in when it exits.
    $null = $Proc.Handle
    $DoneAt = $null
    while (-not $Proc.HasExited) {
        Start-Sleep -Seconds 15
        if ($null -eq $DoneAt -and (Test-Path -LiteralPath $UatLog) -and (Select-String -Path $UatLog -Pattern "LogCook: Display: Done!" -Quiet)) {
            $DoneAt = Get-Date
        }
        if ($null -ne $DoneAt -and ((Get-Date) - $DoneAt).TotalSeconds -gt $CookHangSeconds) {
            $Cooks = Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor-Cmd.exe'" |
                Where-Object { $_.CommandLine -match "Ginnungagap" -and $_.CommandLine -match "-run=Cook" }
            foreach ($Cook in $Cooks) {
                Write-Host "Cook commandlet $($Cook.ProcessId) still alive $CookHangSeconds s after Done: killing it (the cooked data is complete)."
                Stop-Process -Id $Cook.ProcessId -Force -ErrorAction SilentlyContinue
            }
            $DoneAt = $null
        }
    }
    Get-Content -LiteralPath $UatLog | Select-String -Pattern "BUILD SUCCESSFUL|BUILD FAILED|AutomationTool exiting with ExitCode" | ForEach-Object { Write-Host $_.Line }
    return $Proc.ExitCode
}

$Code = 0
if (-not $StageOnly) {
    $Code = Invoke-BuildCookRun @("-build", "-cook") "PackageCorvette_Cook.txt"
    if ($Code -ne 0) {
        Write-Host "BuildCookRun exited with $Code after the cook (a hung commandlet, most likely): staging what was cooked."
    }
}
if ($StageOnly -or $Code -ne 0) {
    $Code = Invoke-BuildCookRun @("-skipbuild", "-skipcook") "PackageCorvette_Stage.txt"
}
if ($Code -ne 0) { throw "BuildCookRun failed with exit code $Code" }
Write-Host "Packaged to $ArchiveDirectory"
