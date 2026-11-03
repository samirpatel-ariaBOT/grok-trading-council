param(
    [Parameter(Mandatory=$true)][string]$ExpectedVolumeUniqueId,
    [switch]$CollectPublic
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = 'D:\GrokTradingCouncil'
$ActualRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path.TrimEnd('\')
if ($ActualRoot -ine $ProjectRoot) { throw "Launch this fresh checkout from $ProjectRoot. No C: fallback." }
$ProjectVolume = Get-Volume -DriveLetter D
if ($ProjectVolume.UniqueId -cne $ExpectedVolumeUniqueId) { throw 'D: volume identity does not match the intended portable drive.' }
if ($ProjectVolume.HealthStatus -ne 'Healthy') { throw 'D: volume is not healthy.' }
if ((Get-Item $ProjectRoot).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'The project root must not redirect through a junction or link.' }
$Probe = Join-Path $ProjectRoot ('.write-probe-' + [guid]::NewGuid().ToString())
try { [IO.File]::WriteAllText($Probe, 'GTC write check'); if ((Get-Content $Probe) -ne 'GTC write check') { throw 'Write check failed.' } }
finally { if (Test-Path $Probe) { Remove-Item -LiteralPath $Probe } }
foreach ($Relative in @('runtime','runtime\tmp','runtime\pip-cache','runtime\pycache')) {
    $Destination = Join-Path $ProjectRoot $Relative
    if (Test-Path $Destination) {
        if ((Get-Item $Destination).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked storage is not allowed: $Relative" }
    } else { New-Item -ItemType Directory -Path $Destination | Out-Null }
}
$env:TEMP = Join-Path $ProjectRoot 'runtime\tmp'
$env:TMP = $env:TEMP
$env:PIP_CACHE_DIR = Join-Path $ProjectRoot 'runtime\pip-cache'
$env:PYTHONPYCACHEPREFIX = Join-Path $ProjectRoot 'runtime\pycache'
$env:PYTHONNOUSERSITE = '1'
$env:GTC_VERIFIED_D_VOLUME = $ProjectVolume.UniqueId
$ProjectPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $ProjectPython)) {
    if (Test-Path (Join-Path $ProjectRoot '.venv')) { throw 'Incomplete environment exists. Inspect it; this launcher will not replace it.' }
    py -3 -m venv (Join-Path $ProjectRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Environment creation failed.' }
}
if ((Get-Item (Join-Path $ProjectRoot '.venv')).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Environment must be physically on D:.' }
Set-Location $ProjectRoot
& $ProjectPython -m pip install -r requirements-dev.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
if ($CollectPublic) { & $ProjectPython scripts\collect_public.py }
else { & $ProjectPython scripts\run.py --demo }
exit $LASTEXITCODE
