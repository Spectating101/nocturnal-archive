Param(
    [string]$Channel = $env:NOCTURNAL_CHANNEL,
    [string]$PackageSpec = $env:NOCTURNAL_PACKAGE_SPEC,
    [string]$PythonCmd = $env:NOCTURNAL_PYTHON,
    [string]$InstallRoot = $env:NOCTURNAL_HOME,
    [string]$ExtraIndexUrl = $env:NOCTURNAL_EXTRA_INDEX_URL,
    [string]$SetupFlags = $env:NOCTURNAL_SETUP_FLAGS,
    [string]$PackageSha256 = $env:NOCTURNAL_PACKAGE_SHA256
)

if (-not $Channel) { $Channel = "beta" }
if (-not $PackageSpec) { $PackageSpec = "nocturnal-archive" }
if (-not $PythonCmd) { $PythonCmd = "python" }
if (-not $InstallRoot) { $InstallRoot = Join-Path $env:USERPROFILE ".nocturnal_archive" }

$VenvDir = Join-Path $InstallRoot "venv"
$ScriptsDir = Join-Path $VenvDir "Scripts"

function Log($Message) {
    Write-Host "[nocturnal-install] $Message"
}

function Fail($Message) {
    Write-Error "[nocturnal-install] $Message"
    exit 1
}

if (-not (Get-Command $PythonCmd -ErrorAction SilentlyContinue)) {
    Fail "Python not found. Install Python 3.9+ first."
}

Log "Creating install directory at $InstallRoot"
New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null

if (-not (Test-Path $VenvDir)) {
    Log "Creating virtual environment"
    & $PythonCmd -m venv $VenvDir | Out-Null
}

$ActivateScript = Join-Path $ScriptsDir "Activate.ps1"
. $ActivateScript

Log "Upgrading pip"
python -m pip install --upgrade pip | Out-Null

$installArgs = @("install", $PackageSpec)
if (-not [string]::IsNullOrWhiteSpace($PackageSha256)) {
    Log "Downloading package for hash verification"
    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName())
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    try {
        $downloadArgs = @("download", $PackageSpec, "--no-deps", "--dest", $tempDir)
        if ($Channel -ne "stable") {
            $downloadArgs += "--pre"
        }
        if ($ExtraIndexUrl) {
            $downloadArgs += "--extra-index-url"
            $downloadArgs += $ExtraIndexUrl
        }
        pip @downloadArgs | Out-Null

        $artifact = Get-ChildItem -Path $tempDir -File | Sort-Object Name | Select-Object -First 1
        if (-not $artifact) {
            Fail "Downloaded package artifact not found for hash verification"
        }

        $calculated = (Get-FileHash -Algorithm SHA256 -Path $artifact.FullName).Hash.ToLowerInvariant()
        if ($calculated -ne $PackageSha256.ToLowerInvariant()) {
            Fail "Hash mismatch for $PackageSpec (expected $PackageSha256, got $calculated)"
        }

        Log "Hash verified for $($artifact.Name)"
        Log "Installing verified artifact"
        pip install $artifact.FullName | Out-Null
    }
    finally {
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
else {
    if ($Channel -ne "stable") {
        $installArgs += "--pre"
    }
    if ($ExtraIndexUrl) {
        $installArgs += "--extra-index-url"
        $installArgs += $ExtraIndexUrl
    }

    Log "Installing $PackageSpec ($Channel channel)"
    pip @installArgs | Out-Null
}

Log "Running nocturnal setup"
$env:NOCTURNAL_ONBOARDING_MODE = "beta"
& (Join-Path $ScriptsDir "nocturnal.exe") --setup $SetupFlags

Log "Launch the agent any time with: $(Join-Path $ScriptsDir "nocturnal.exe")"
