#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Context Engineer environment bootstrap for Windows PowerShell / PowerShell 7.
    Bootstrap do ambiente Context Engineer para Windows PowerShell / PowerShell 7.

.DESCRIPTION
    EN: Creates (or updates) the local .venv using either uv or python -m venv.
        The script reuses the existing environment unless -Force is provided.
    PT: Cria (ou atualiza) o .venv local usando uv ou python -m venv.
        O script reutiliza o ambiente existente a menos que -Force seja fornecido.

.PARAMETER ProjectPath
    EN: Project root. Defaults to the folder where this script lives.
    PT: Raiz do projeto. Padrão é a pasta onde este script está localizado.

.PARAMETER Force
    EN: Recreates the virtual environment from scratch.
    PT: Recria o ambiente virtual do zero.

.PARAMETER SkipUv
    EN: Forces the use of python -m venv even if uv is installed.
    PT: Força o uso de python -m venv mesmo se uv estiver instalado.
#>

[CmdletBinding()]
param(
    [string]$ProjectPath = (Split-Path -Parent $MyInvocation.MyCommand.Path),
    [switch]$Force,
    [switch]$SkipUv
)

$ErrorActionPreference = "Stop"

function Resolve-ProjectPath {
    param([string]$Path)

    if (-not $Path) {
        throw "Project path cannot be empty."
    }

    $resolved = Resolve-Path -LiteralPath $Path -ErrorAction Stop
    return $resolved.Path
}

function Get-Python311 {
    if (Get-Command pyenv -ErrorAction SilentlyContinue) {
        Write-Host "pyenv detected. Using pyenv-managed Python..." -ForegroundColor Cyan
        $available = (& pyenv versions --bare) |
            Where-Object { $_ -match '^3\.11' } |
            Sort-Object |
            Select-Object -Last 1

        if (-not $available) {
            Write-Host "Python 3.11 not found via pyenv. Installing 3.11.14..." -ForegroundColor Yellow
            pyenv install 3.11.14
            $available = "3.11.14"
        }

        pyenv local $available | Out-Null
        pyenv rehash | Out-Null

        $exe = (& pyenv which python).Trim()
        return @{ Command = "python"; Executable = $exe; Version = $available }
    }

    foreach ($candidate in @("py", "python", "python3")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            $version = (& $candidate --version 2>&1)
            if ($version -match '3\.1[1-9]') {
                $exe = (& $candidate -c "import sys; print(sys.executable)" 2>&1).Trim()
                return @{ Command = $candidate; Executable = $exe; Version = $version }
            }
        }
    }

    throw "Python 3.11+ was not found. Install Python (or pyenv-win) and rerun this script."
}

function Ensure-Venv {
    param(
        [string]$ProjectDir,
        [hashtable]$Python,
        [bool]$UseUv,
        [bool]$ForceRecreate
    )

    $venvDir = Join-Path $ProjectDir ".venv"
    $venvPython = Join-Path $venvDir "Scripts\python.exe"

    if (Test-Path $venvDir -and $ForceRecreate) {
        Write-Host "Removing existing .venv (force)..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvDir
    }

    if (-not (Test-Path $venvDir)) {
        if ($UseUv) {
            $args = @("venv", "--python", $Python.Executable)
            if ($ForceRecreate) { $args += "--force" }
            Write-Host "Creating .venv with uv..." -ForegroundColor Cyan
            & uv @args
        }
        else {
            Write-Host "Creating .venv with python -m venv..." -ForegroundColor Cyan
            & $Python.Executable -m venv $venvDir
        }
    }
    else {
        Write-Host ".venv already exists. Reusing environment." -ForegroundColor Yellow
    }

    if (-not (Test-Path $venvPython)) {
        throw "Virtual environment python executable not found at $venvPython"
    }

    return $venvPython
}

function Install-Dependencies {
    param(
        [string]$VenvPython,
        [bool]$UseUv,
        [string]$RequirementsPath
    )

    if ($UseUv) {
        Write-Host "Installing dependencies with uv pip..." -ForegroundColor Cyan
        & uv pip install --python $VenvPython --upgrade pip
        if (Test-Path $RequirementsPath) {
            & uv pip install --python $VenvPython -r $RequirementsPath
        }
        else {
            Write-Warning "requirements.txt not found. Skipping dependency install."
        }
    }
    else {
        Write-Host "Installing dependencies with pip..." -ForegroundColor Cyan
        & $VenvPython -m pip install --upgrade pip
        if (Test-Path $RequirementsPath) {
            & $VenvPython -m pip install -r $RequirementsPath
        }
        else {
            Write-Warning "requirements.txt not found. Skipping dependency install."
        }
    }
}

$projectDir = Resolve-ProjectPath $ProjectPath
Set-Location $projectDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Context Engineer :: PowerShell Setup" -ForegroundColor Green
Write-Host "Context Engineer :: Configuração PowerShell" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Project path / Caminho do projeto: $projectDir" -ForegroundColor Gray

$pythonInfo = Get-Python311
Write-Host "[INFO] Using Python / Usando Python => $($pythonInfo.Executable)" -ForegroundColor Gray

$uvAvailable = (Get-Command uv -ErrorAction SilentlyContinue) -and (-not $SkipUv.IsPresent)
if ($uvAvailable) {
    Write-Host "[INFO] uv detected. Will prefer uv for venv + pip." -ForegroundColor Green
    Write-Host "[INFO] uv detectado. Preferirá uv para venv + pip." -ForegroundColor Green
}
else {
    Write-Host "[WARN] uv not available (or skipped). Falling back to python -m venv." -ForegroundColor Yellow
    Write-Host "[WARN] uv não disponível (ou ignorado). Usando python -m venv." -ForegroundColor Yellow
}

$venvPython = Ensure-Venv -ProjectDir $projectDir -Python $pythonInfo -UseUv:$uvAvailable -ForceRecreate:$Force.IsPresent
Install-Dependencies -VenvPython $venvPython -UseUv:$uvAvailable -RequirementsPath (Join-Path $projectDir "requirements.txt")

$activateScript = Join-Path (Split-Path $venvPython -Parent) "Activate.ps1"

Write-Host ""
Write-Host "[ OK ] Setup completed successfully! / Setup concluído com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the virtual environment run / Para ativar o ambiente virtual execute:" -ForegroundColor Gray
Write-Host "  & '$activateScript'" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or run commands without activating / Ou execute comandos sem ativar:" -ForegroundColor Gray
Write-Host "  uv run python -m cli.main --help" -ForegroundColor Cyan
Write-Host ""
