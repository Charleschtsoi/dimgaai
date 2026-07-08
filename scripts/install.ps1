# dimgaai one-line installer (Windows)
# Usage:
#   irm https://raw.githubusercontent.com/Charleschtsoi/dimgaai/main/scripts/install.ps1 | iex
#
# Or save and run:
#   .\scripts\install.ps1

$ErrorActionPreference = "Stop"
$Repo = "Charleschtsoi/dimgaai"
$Branch = "main"
$ZipUrl = "https://github.com/$Repo/archive/refs/heads/$Branch.zip"
$InstallHome = Join-Path $env:LOCALAPPDATA "dimgaai"
$CacheDir = Join-Path $InstallHome "installer-cache"

function Test-PythonExe([string]$Exe, [string[]]$PrefixArgs = @()) {
    if (-not (Test-Path $Exe)) { return $false }
    try {
        & $Exe @($PrefixArgs + @("-c", "import sys; print(sys.version_info[:2] >= (3,11))")) 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Get-DimgaaiPython {
    $paths = @(
        @{ Exe = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue); Args = @() },
        @{ Exe = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"; Args = @() },
        @{ Exe = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"; Args = @() }
    )
    foreach ($item in $paths) {
        if ($item.Exe -and (Test-PythonExe $item.Exe $item.Args)) {
            return $item
        }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        if (Test-PythonExe "py" @("-3")) {
            return @{ Exe = "py"; Args = @("-3") }
        }
    }
    return $null
}

Write-Host ""
Write-Host "dimgaai installer" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""

$py = Get-DimgaaiPython
if (-not $py) {
    Write-Error "Python 3.11+ not found. Install from https://www.python.org/downloads/"
}

$pipArgs = @($py.Args + @("-m", "pip", "install", "--upgrade"))

# Prefer pip install from GitHub (needs git). Fall back to zip download (no git).
$installed = $false
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "Installing dimgaai CLI from GitHub (git)..." -ForegroundColor Yellow
    & $py.Exe @($pipArgs + @("git+https://github.com/$Repo.git#subdirectory=backend"))
    if ($LASTEXITCODE -eq 0) { $installed = $true }
}

if (-not $installed) {
    Write-Host "Installing dimgaai CLI from zip (no git required)..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $CacheDir | Out-Null
    $zipPath = Join-Path $CacheDir "dimgaai.zip"
    $extractPath = Join-Path $CacheDir "extract"
    if (Test-Path $extractPath) { Remove-Item -Recurse -Force $extractPath }
    Invoke-WebRequest -Uri $ZipUrl -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
    $repoDir = Get-ChildItem $extractPath -Directory | Select-Object -First 1
    if (-not $repoDir) { Write-Error "Downloaded archive was empty." }
  $backendDir = Join-Path $repoDir.FullName "backend"
    & $py.Exe @($pipArgs + @($backendDir))
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host ""
Write-Host "Starting dimgaai (downloads app + opens browser on first run)..." -ForegroundColor Green
Write-Host ""

& $py.Exe @($py.Args + @("-m", "dimgaai_cli", "go"))
exit $LASTEXITCODE
