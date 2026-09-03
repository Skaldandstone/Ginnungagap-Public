param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

$sourcePath = Join-Path $ProjectRoot 'docs\concept-art\player-suits\standard-suit-turnaround.png'
$workspace = Join-Path $ProjectRoot 'Art\Characters\PlayerSuits\RealityScan\V25_ConceptLock'
$inputPath = Join-Path $workspace 'Input'
$componentPath = Join-Path $workspace 'Components'

New-Item -ItemType Directory -Path $inputPath -Force | Out-Null
New-Item -ItemType Directory -Path $componentPath -Force | Out-Null

Add-Type -AssemblyName System.Drawing
$source = [System.Drawing.Bitmap]::FromFile($sourcePath)
try {
    if ($source.Width -ne 1536 -or $source.Height -ne 1024) {
        throw "Unexpected turnaround dimensions: $($source.Width)x$($source.Height)"
    }

    # Center each subject independently and exclude neighboring-view fragments.
    $views = @(
        @{ Name = '00_front.png'; X = 54 },
        @{ Name = '01_profile.png'; X = 502 },
        @{ Name = '02_rear.png'; X = 978 }
    )

    foreach ($view in $views) {
        $rect = [System.Drawing.Rectangle]::new($view.X, 0, 512, 1024)
        $crop = $source.Clone($rect, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
        try {
            $destination = Join-Path $inputPath $view.Name
            $crop.Save($destination, [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally {
            $crop.Dispose()
        }
    }
}
finally {
    $source.Dispose()
}

$manifest = [ordered]@{
    version = 25
    purpose = 'RealityScan concept-lock alignment experiment'
    source = $sourcePath
    input_directory = $inputPath
    views = @('00_front.png', '01_profile.png', '02_rear.png')
    caveat = 'Painted orthographic views are not photogrammetric captures; require one coherent multi-camera component before reconstruction.'
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $workspace 'DatasetManifest.json') -Encoding utf8

Write-Output $workspace
