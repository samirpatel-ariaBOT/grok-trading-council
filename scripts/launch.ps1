param(
    [Parameter(Mandatory=$true)][string]$ExpectedVolumeUniqueId,
    [switch]$Setup,
    [switch]$CollectPublic
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = 'D:\GrokTradingCouncil'
$ProjectId = 'gtc-fresh-20261102'

function Assert-LocalPath {
    param([Parameter(Mandatory=$true)][string]$Path)
    $Full = [IO.Path]::GetFullPath($Path)
    if (-not ($Full -ieq $ProjectRoot -or
              $Full.StartsWith($ProjectRoot + '\', [StringComparison]::OrdinalIgnoreCase))) {
        throw "Storage path is outside the verified project root: $Path"
    }
    $Current = $ProjectRoot
    $Parts = $Full.Substring($ProjectRoot.Length).TrimStart('\')
    if (Test-Path -LiteralPath $Current) {
        if ((Get-Item -LiteralPath $Current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Linked storage is not allowed: $Current"
        }
    }
    if ($Parts) {
        foreach ($Part in ($Parts -split '\\')) {
            $Current = Join-Path $Current $Part
            if (Test-Path -LiteralPath $Current) {
                if ((Get-Item -LiteralPath $Current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                    throw "Linked storage is not allowed: $Current"
                }
            }
        }
    }
}

if ([string]::IsNullOrWhiteSpace($ExpectedVolumeUniqueId)) {
    throw 'Supply the independently verified D: volume UniqueId.'
}
$ProjectVolume = Get-Volume -DriveLetter D
if ($ProjectVolume.UniqueId -cne $ExpectedVolumeUniqueId) {
    throw 'D: volume identity does not match the intended portable drive.'
}
if ($ProjectVolume.HealthStatus -ne 'Healthy') {
    throw 'D: volume is not healthy.'
}
if ($ProjectVolume.FileSystem -notin @('NTFS', 'ReFS')) {
    throw 'The demo SQLite WAL requires a verified local NTFS or ReFS volume. No fallback.'
}
$MinimumFree = if ($Setup) { 512MB } else { 128MB }
if ($ProjectVolume.SizeRemaining -lt $MinimumFree) {
    throw 'Insufficient free space on the verified D: volume.'
}

# Validate the actual checkout before any project-controlled writes.
if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "Expected checkout not found: $ProjectRoot"
}
Assert-LocalPath $ProjectRoot
Assert-LocalPath (Join-Path $ProjectRoot 'scripts')
$ActualRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).ProviderPath.TrimEnd('\')
if ($ActualRoot -ine $ProjectRoot) {
    throw "Launch this fresh checkout from $ProjectRoot. No C: fallback."
}

$Marker = Join-Path $ProjectRoot '.project-id'
Assert-LocalPath $Marker
if (-not (Test-Path -LiteralPath $Marker -PathType Leaf) -or
    (Get-Content -LiteralPath $Marker -Raw).Trim() -cne $ProjectId) {
    throw 'GTC project identity marker is missing or mismatched.'
}

$Requirements = Join-Path $ProjectRoot 'requirements-dev.lock.txt'
Assert-LocalPath $Requirements
if (-not (Test-Path -LiteralPath $Requirements -PathType Leaf)) {
    throw 'Pinned dependency list is missing.'
}

foreach ($Relative in @(
    '.venv', '.venv\Scripts', '.venv\Scripts\python.exe',
    'runtime', 'runtime\tmp', 'runtime\pip-cache', 'runtime\pycache',
    'runtime\demo.sqlite', 'runtime\demo.sqlite-wal', 'runtime\demo.sqlite-shm',
    'runtime\backups', 'runtime\public_readonly'
)) {
    Assert-LocalPath (Join-Path $ProjectRoot $Relative)
}

# All project-controlled environment and cache locations stay on D:.
foreach ($Relative in @('runtime', 'runtime\tmp', 'runtime\pip-cache', 'runtime\pycache')) {
    $Destination = Join-Path $ProjectRoot $Relative
    if (-not (Test-Path -LiteralPath $Destination)) {
        New-Item -ItemType Directory -Path $Destination | Out-Null
    }
}
$env:TEMP = Join-Path $ProjectRoot 'runtime\tmp'
$env:TMP = $env:TEMP
$env:PIP_CACHE_DIR = Join-Path $ProjectRoot 'runtime\pip-cache'
$env:PYTHONPYCACHEPREFIX = Join-Path $ProjectRoot 'runtime\pycache'
$env:PYTHONNOUSERSITE = '1'
$env:GTC_VERIFIED_D_VOLUME = $ProjectVolume.UniqueId

$ProjectPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
Set-Location $ProjectRoot
if ($Setup) {
    if (-not (Test-Path -LiteralPath $ProjectPython -PathType Leaf)) {
        if (Test-Path -LiteralPath (Join-Path $ProjectRoot '.venv')) {
            throw 'Incomplete environment exists; inspect manually. Nothing was deleted.'
        }
        py -3.12 -c "import sys; assert sys.version_info[:2] == (3, 12)"
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required for setup.' }
        py -3.12 -m venv (Join-Path $ProjectRoot '.venv')
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 environment creation failed.' }
    }
} elseif (-not (Test-Path -LiteralPath $ProjectPython -PathType Leaf)) {
    throw 'Environment missing. Run this launcher once with -Setup after reviewing the pinned dependencies.'
}
Assert-LocalPath $ProjectPython

& $ProjectPython -I -c "import sys; assert sys.version_info[:2] == (3, 12); assert sys.prefix != sys.base_prefix"
if ($LASTEXITCODE -ne 0) {
    throw 'Existing project environment is not an isolated Python 3.12 environment.'
}

if ($Setup) {
    & $ProjectPython -m pip install -r $Requirements
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}

# Check exact declared pins, not just whether pip reports healthy dependencies.
$PinCheck = @'
import importlib.metadata as metadata
import pathlib
import sys
failures = []
for row in pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    row = row.strip()
    if not row or row.startswith("#"):
        continue
    if row.count("==") != 1:
        failures.append("Unsupported requirement: " + row)
        continue
    name, wanted = row.split("==", 1)
    try:
        actual = metadata.version(name)
    except metadata.PackageNotFoundError:
        actual = "<missing>"
    if actual != wanted:
        failures.append(f"{name}: expected {wanted}, installed {actual}")
if failures:
    print("\n".join(failures), file=sys.stderr)
    sys.exit(2)
'@
& $ProjectPython -I -c $PinCheck $Requirements
if ($LASTEXITCODE -ne 0) {
    throw 'Pinned dependencies differ. Run -Setup to repair after review.'
}
& $ProjectPython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Python dependency consistency check failed.' }

if ($Setup) {
    Write-Host 'GTC Python 3.12 environment and pinned dependencies verified on D:. No demo was started.'
    exit 0
}
if ($CollectPublic) {
    & $ProjectPython scripts\collect_public.py
} else {
    & $ProjectPython scripts\run.py --demo
}
exit $LASTEXITCODE
