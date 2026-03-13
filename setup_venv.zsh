#!/usr/bin/env zsh
# Context Engineer - Zsh setup script
# Script de setup Context Engineer para Zsh
# Compatible with macOS and Linux (including WSL distros using zsh)
# Compatível com macOS e Linux (incluindo distros WSL usando zsh)

set -euo pipefail

CURRENT_DIR=$(cd -- "$(dirname "$0")" && pwd)
PROJECT_DIR=${1:-$CURRENT_DIR}

log() {
  local color=$1
  shift
  case $color in
    info) printf "\033[36m[INFO]\033[0m %s\n" "$*" ;;
    warn) printf "\033[33m[WARN]\033[0m %s\n" "$*" ;;
    error) printf "\033[31m[ERR ]\033[0m %s\n" "$*" ;;
    success) printf "\033[32m[ OK ]\033[0m %s\n" "$*" ;;
    *) printf "%s\n" "$*" ;;
  esac
}

if [[ ! -d "$PROJECT_DIR" ]]; then
  log error "Project directory not found / Diretório do projeto não encontrado: $PROJECT_DIR"
  exit 1
fi

cd "$PROJECT_DIR"
echo "=========================================="
echo "Context Engineer :: Zsh Setup"
echo "Context Engineer :: Configuração Zsh"
echo "=========================================="
echo ""
log info "Project path / Caminho do projeto: $PROJECT_DIR"

ensure_pyenv_python() {
  if command -v pyenv >/dev/null 2>&1; then
    log info "pyenv detected. Using pyenv-managed Python / pyenv detectado. Usando Python gerenciado pelo pyenv..."
    local python_version
    python_version=$(pyenv versions --bare | grep '^3\.11' | sort -V | tail -1)
    if [[ -z "${python_version}" ]]; then
      log warn "Python 3.11 not found via pyenv. Installing 3.11.14 / Python 3.11 não encontrado via pyenv. Instalando 3.11.14..."
      pyenv install 3.11.14
      python_version="3.11.14"
    fi
    pyenv local "$python_version"
    pyenv rehash >/dev/null
    log success "Python version set to / Versão Python definida para: $(pyenv version-name)"
    PYTHON_CMD="python"
    PYTHON_BIN=$(pyenv which python)
    return 0
  fi
  return 1
}

ensure_system_python() {
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      local version
      version=$($candidate --version 2>&1)
      if [[ "$version" =~ 3\.1[1-9] ]]; then
        log success "Using system Python / Usando Python do sistema: $version"
        PYTHON_CMD="$candidate"
        PYTHON_BIN=$($candidate -c 'import sys; print(sys.executable)')
        return 0
      fi
    fi
  done
  return 1
}

PYTHON_CMD=""
PYTHON_BIN=""
if ! ensure_pyenv_python && ! ensure_system_python; then
  log error "Python 3.11+ not found. Install it (pyenv or system) and rerun / Python 3.11+ não encontrado. Instale (pyenv ou sistema) e execute novamente."
  exit 1
fi

log info "Python executable / Executável Python: $PYTHON_BIN"

VENV_DIR="$PROJECT_DIR/.venv"
USE_UV=true
if ! command -v uv >/dev/null 2>&1; then
  log warn "uv not found. Falling back to python -m venv / uv não encontrado. Usando python -m venv"
  USE_UV=false
fi

create_venv() {
  if [[ "$USE_UV" == true ]]; then
    log info "Creating virtual environment with uv / Criando ambiente virtual com uv..."
    uv venv --python "$PYTHON_BIN"
  else
    log info "Creating virtual environment with python -m venv / Criando ambiente virtual com python -m venv..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
}

if [[ -d "$VENV_DIR" ]]; then
  log warn ".venv already exists. Reusing environment / .venv já existe. Reutilizando ambiente."
else
  create_venv
fi

ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
if [[ ! -f "$ACTIVATE_SCRIPT" ]]; then
  log error "Activation script not found at / Script de ativação não encontrado em: $ACTIVATE_SCRIPT"
  exit 1
fi

install_dependencies() {
  if [[ "$USE_UV" == true ]]; then
    log info "Installing dependencies with uv / Instalando dependências com uv..."
    source "$ACTIVATE_SCRIPT"
    uv pip install --upgrade pip
    if [[ -f "requirements.txt" ]]; then
      uv pip install -r requirements.txt
    else
      log warn "requirements.txt not found. Skipping dependency install / requirements.txt não encontrado. Pulando instalação de dependências."
    fi
  else
    log info "Installing dependencies with pip / Instalando dependências com pip..."
    source "$ACTIVATE_SCRIPT"
    pip install --upgrade pip
    if [[ -f "requirements.txt" ]]; then
      pip install -r requirements.txt
    else
      log warn "requirements.txt not found. Skipping dependency install / requirements.txt não encontrado. Pulando instalação de dependências."
    fi
  fi
}

install_dependencies

log success "Setup completed successfully! / Setup concluído com sucesso!"
printf "\nTo activate the environment run / Para ativar o ambiente execute:\n"
printf "  source $ACTIVATE_SCRIPT\n"
printf "\nOr run commands without activating / Ou execute comandos sem ativar:\n"
printf "  uv run python -m cli.main --help\n"
