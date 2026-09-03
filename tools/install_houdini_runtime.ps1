[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string]$SettingsFile,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
    [string]$EulaDate,

    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$HoudiniVersion = '22.0.423',

    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string]$LauncherInstallerPath
)

$ErrorActionPreference = 'Stop'
$launcherCli = 'C:\Program Files\Side Effects Software\Launcher\bin\houdini_installer.exe'

function Assert-SideFxSignature {
    param([Parameter(Mandatory = $true)][string]$Path)

    $signature = Get-AuthenticodeSignature -LiteralPath $Path
    if ($signature.Status -ne 'Valid') {
        throw "SideFX executable signature is not valid: $Path ($($signature.Status))"
    }

    $subject = $signature.SignerCertificate.Subject
    if ($subject -notmatch 'Side Effects Software') {
        throw "Unexpected executable signer for ${Path}: $subject"
    }
}

if ($LauncherInstallerPath) {
    $resolvedLauncherInstaller = (Resolve-Path -LiteralPath $LauncherInstallerPath).Path
    Assert-SideFxSignature -Path $resolvedLauncherInstaller

    if ($PSCmdlet.ShouldProcess($resolvedLauncherInstaller, 'Install the SideFX Launcher silently')) {
        $launcherProcess = Start-Process `
            -FilePath $resolvedLauncherInstaller `
            -ArgumentList '/S' `
            -Wait `
            -PassThru `
            -WindowStyle Hidden

        if ($launcherProcess.ExitCode -ne 0) {
            throw "SideFX Launcher installation failed with exit code $($launcherProcess.ExitCode)."
        }
    }
}

if (-not (Test-Path -LiteralPath $launcherCli -PathType Leaf)) {
    throw @"
The SideFX Launcher CLI was not found at:
$launcherCli

Download the signed Windows launcher from https://www.sidefx.com/download/, then rerun this script with -LauncherInstallerPath.
"@
}

Assert-SideFxSignature -Path $launcherCli
$resolvedSettings = (Resolve-Path -LiteralPath $SettingsFile).Path
$product = 'Houdini'
$installArguments = "install -q --product `"$product`" --version `"$HoudiniVersion`" --settings-file `"$resolvedSettings`" --accept-EULA `"$EulaDate`""

if ($PSCmdlet.ShouldProcess("$product $HoudiniVersion", 'Install with the official SideFX CLI')) {
    $houdiniProcess = Start-Process `
        -FilePath $launcherCli `
        -ArgumentList $installArguments `
        -Wait `
        -PassThru `
        -WindowStyle Hidden

    if ($houdiniProcess.ExitCode -ne 0) {
        throw "Houdini installation failed with exit code $($houdiniProcess.ExitCode)."
    }
}

$expectedInstall = "C:\Program Files\Side Effects Software\Houdini $HoudiniVersion"
if (-not (Test-Path -LiteralPath $expectedInstall -PathType Container)) {
    throw "The installer returned success, but the expected installation was not found: $expectedInstall"
}

Write-Output "Installed $product $HoudiniVersion at $expectedInstall"
Write-Output 'Restart Unreal Editor before validating the Houdini Engine session.'
