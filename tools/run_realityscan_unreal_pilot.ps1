[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InputDirectory,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9_]+$')]
    [string]$AssetName,

    [string]$OutputDirectory,

    [ValidateRange(1000, 2000000)]
    [int]$TargetTriangleCount = 100000,

    [ValidateRange(0.1, 1.0)]
    [double]$MinimumRegisteredFraction = 0.9
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$resolvedInput = (Resolve-Path -LiteralPath $InputDirectory).Path
$images = @(Get-ChildItem -LiteralPath $resolvedInput -File | Where-Object {
    $_.Extension -in '.png', '.jpg', '.jpeg', '.tif', '.tiff'
})
if ($images.Count -lt 8) {
    throw "RealityScan requires at least eight input frames for this pipeline; found $($images.Count)."
}

$realityScan = 'C:\Program Files\Epic Games\RealityScan_2.2\RealityScan.exe'
if (-not (Test-Path -LiteralPath $realityScan)) {
    $manifestRoot = 'C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests'
    $manifest = Get-ChildItem -LiteralPath $manifestRoot -Filter '*.item' -ErrorAction SilentlyContinue |
        Where-Object { Select-String -LiteralPath $_.FullName -Pattern '"DisplayName": "RealityScan' -Quiet } |
        Select-Object -First 1
    if (-not $manifest) {
        throw 'RealityScan installation was not found.'
    }
    $manifestData = Get-Content -LiteralPath $manifest.FullName -Raw | ConvertFrom-Json
    $realityScan = Join-Path $manifestData.InstallLocation $manifestData.LaunchExecutable
}
if (-not (Test-Path -LiteralPath $realityScan)) {
    throw "RealityScan executable is missing: $realityScan"
}

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path (Split-Path -Parent $resolvedInput) 'RealityScanOutput'
}
$resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null

$projectPath = Join-Path $resolvedOutput "$AssetName.rsproj"
$modelPath = Join-Path $resolvedOutput "$AssetName.obj"
$overviewPath = Join-Path $resolvedOutput 'AlignmentOverview.html'
$gatePath = Join-Path $resolvedOutput 'RealityScanGate.json'
$overviewTemplate = Join-Path (Split-Path -Parent $realityScan) 'Reports\Overview.html'

function Invoke-RealityScan {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [Parameter(Mandatory = $true)]
        [string]$LogPath
    )

    $errorLogPath = [System.IO.Path]::ChangeExtension($LogPath, '.error.log')
    $argumentLine = ($Arguments | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + $_.Replace('"', '\"') + '"'
        }
        else {
            $_
        }
    }) -join ' '

    $process = Start-Process -FilePath $realityScan `
        -ArgumentList $argumentLine `
        -RedirectStandardOutput $LogPath `
        -RedirectStandardError $errorLogPath `
        -WindowStyle Hidden `
        -Wait `
        -PassThru
    if ($process.ExitCode -ne 0) {
        throw "RealityScan exited with code $($process.ExitCode). See $LogPath and $errorLogPath."
    }
}

$reconstructionLog = Join-Path $resolvedOutput 'Reconstruction.log'
Invoke-RealityScan -LogPath $reconstructionLog -Arguments @(
    '-headless',
    '-stdConsole',
    '-newScene',
    '-set', 'appAutoSaveMode=false',
    '-set', 'sfmImagesOverlap=High',
    '-set', 'sfmDetectorSensitivity=Ultra',
    '-addFolder', $resolvedInput,
    '-align',
    '-selectMaximalComponent',
    '-setReconstructionRegionAuto',
    '-calculateNormalModel',
    '-simplify', $TargetTriangleCount.ToString(),
    '-unwrap',
    '-calculateTexture',
    '-exportSelectedModel', $modelPath,
    '-save', $projectPath,
    '-quit'
)

if (-not (Test-Path -LiteralPath $projectPath) -or -not (Test-Path -LiteralPath $modelPath)) {
    throw 'RealityScan did not produce the expected project and OBJ model.'
}

$reportLog = Join-Path $resolvedOutput 'Report.log'
Invoke-RealityScan -LogPath $reportLog -Arguments @(
    '-headless',
    '-stdConsole',
    '-load', $projectPath, 'deleteAutosave',
    '-selectMaximalComponent',
    '-exportReport', $overviewPath, $overviewTemplate,
    '-quit'
)

$deadline = (Get-Date).AddSeconds(10)
while (-not (Test-Path -LiteralPath $overviewPath) -and (Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 100
}
if (-not (Test-Path -LiteralPath $overviewPath)) {
    throw 'RealityScan alignment report was not produced.'
}

$overview = Get-Content -LiteralPath $overviewPath -Raw
$registrationMatches = [regex]::Matches(
    $overview,
    'Count of registered images</th>\s*<td>(\d+)\s*/\s*(\d+)',
    [System.Text.RegularExpressions.RegexOptions]::Singleline)
$components = foreach ($match in $registrationMatches) {
    [pscustomobject]@{
        Registered = [int]$match.Groups[1].Value
        Inputs = [int]$match.Groups[2].Value
    }
}
if (-not $components) {
    throw 'Could not read registered-image counts from RealityScan report.'
}

$largestComponent = $components | Sort-Object Registered -Descending | Select-Object -First 1
$faceCount = 0
$vertexCount = 0
foreach ($line in [System.IO.File]::ReadLines($modelPath)) {
    if ($line.StartsWith('v ')) { $vertexCount++ }
    elseif ($line.StartsWith('f ')) { $faceCount++ }
}
$registeredFraction = $largestComponent.Registered / [double]$largestComponent.Inputs
$passed = $registeredFraction -ge $MinimumRegisteredFraction -and $faceCount -ge 10000

$result = [ordered]@{
    AssetName = $AssetName
    RealityScanExecutable = $realityScan
    InputDirectory = $resolvedInput
    InputImageCount = $images.Count
    ComponentCount = @($components).Count
    LargestComponentRegisteredImages = $largestComponent.Registered
    RegisteredFraction = $registeredFraction
    VertexCount = $vertexCount
    FaceCount = $faceCount
    TargetTriangleCount = $TargetTriangleCount
    ModelPath = $modelPath
    ProjectPath = $projectPath
    AlignmentReport = $overviewPath
    PromotionGate = if ($passed) { 'pass' } else { 'quarantine' }
}
[System.IO.File]::WriteAllText(
    $gatePath,
    ($result | ConvertTo-Json -Depth 4),
    [System.Text.UTF8Encoding]::new($false))

$result | Format-List
if (-not $passed) {
    [Console]::Error.WriteLine("RealityScan promotion gate failed. The output remains quarantined; see $gatePath")
    exit 2
}

Write-Host "RealityScan promotion gate passed: $gatePath"
