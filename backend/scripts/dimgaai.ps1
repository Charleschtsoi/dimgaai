# dimgaai CLI wrapper (run from backend/ or backend/scripts/)
$ErrorActionPreference = "Stop"
$Backend = if ($PSScriptRoot -match "scripts$") {
    Split-Path -Parent $PSScriptRoot
} else {
    $PSScriptRoot
}

function Test-PythonExe([string]$Exe, [string[]]$PrefixArgs = @()) {
    if ($Exe -ne "py" -and -not (Test-Path $Exe)) { return $false }
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
        @{ Exe = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"; Args = @() },
        @{ Exe = "C:\Python312\python.exe"; Args = @() },
        @{ Exe = "C:\Python311\python.exe"; Args = @() }
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

$py = Get-DimgaaiPython
if (-not $py) {
    Write-Error "Python 3.11+ not found. Install from https://www.python.org/downloads/"
}

Push-Location $Backend
try {
    & $py.Exe @($py.Args + @("-m", "dimgaai_cli") + $args)
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
