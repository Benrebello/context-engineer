#!/bin/bash
# Virtual environment setup script for WSL/Linux
# Script de setup do ambiente virtual para WSL/Linux
# Context Engineer - Setup Script
# Supports uv, pyenv, and system default installation
# Suporta uv, pyenv e instalação padrão do sistema

set -e  # Exit on error

echo "=========================================="
echo "Context Engineer :: Virtual Environment Setup"
echo "Context Engineer :: Configuração do Ambiente Virtual"
echo "=========================================="
echo ""

# Check if we're in WSL / Verificar se estamos no WSL
if [ ! -f /proc/version ] || ! grep -q Microsoft /proc/version; then
    echo "[INFO] This script is optimized for WSL. Continuing anyway..."
    echo "[INFO] Este script é otimizado para WSL. Continuando mesmo assim..."
fi

# Caminho do projeto (ajuste se necessário)
PROJECT_DIR="/mnt/c/Users/benjamin.rebello/Documents/projetos/prototipos/ref/context-engineer"

# Navegar para o diretório do projeto
cd "$PROJECT_DIR" || {
    echo "Erro: Não foi possível acessar o diretório do projeto"
    echo "   Caminho: $PROJECT_DIR"
    exit 1
}

# Check if pyenv is available / Verificar se pyenv está disponível
if command -v pyenv &> /dev/null; then
    echo "[INFO] pyenv detected! Using pyenv to manage Python..."
    echo "[INFO] pyenv detectado! Usando pyenv para gerenciar Python..."
    
    # Initialize pyenv if needed / Inicializar pyenv se necessário
    if [ -z "$PYENV_ROOT" ]; then
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
    fi
    
    # Check current version / Verificar versão atual
    CURRENT_VERSION=$(pyenv version-name)
    echo "[INFO] Current Python version / Versão Python atual: $CURRENT_VERSION"
    
    # Check if Python 3.11 is installed / Verificar se Python 3.11 está instalado
    PYTHON_311_VERSION=$(pyenv versions --bare | grep "^3\.11" | sort -V | tail -1 || true)
    
    if [ -z "$PYTHON_311_VERSION" ]; then
        echo "[WARN] Python 3.11 not found via pyenv / Python 3.11 não encontrado via pyenv"
        echo "[INFO] Installing Python 3.11.14 via pyenv / Instalando Python 3.11.14 via pyenv..."
        
        # Instalar dependências de build se necessário
        if ! dpkg -l | grep -q libssl-dev; then
            echo "Instalando dependências de build..."
            sudo apt-get update -qq
            sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
              libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
              libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev
        fi
        
        pyenv install 3.11.14
        pyenv local 3.11.14
        pyenv rehash
    else
        # Use most recent Python 3.11 available / Usar Python 3.11 mais recente disponível
        echo "[INFO] Using Python $PYTHON_311_VERSION / Usando Python $PYTHON_311_VERSION"
        pyenv local "$PYTHON_311_VERSION"
    fi
    
    # Check Python / Verificar Python
    PYTHON_CMD="python"
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    echo "[INFO] Python in use / Python em uso: $PYTHON_VERSION"
    
else
    echo "[INFO] pyenv not found. Using system Python / pyenv não encontrado. Usando Python do sistema..."
    
    # Check if python3-venv is available / Verificar se python3-venv está disponível
    if ! python3 -m venv --help &> /dev/null; then
        echo "[INFO] Installing python3-venv / Instalando python3-venv..."
        sudo apt-get update -qq
        sudo apt-get install -y python3.12-venv python3-pip || \
        sudo apt-get install -y python3.11-venv python3-pip || \
        sudo apt-get install -y python3-venv python3-pip
    fi
    
    PYTHON_CMD="python3"
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    echo "[INFO] Python in use / Python em uso: $PYTHON_VERSION"
fi

# Check if uv is available / Verificar se uv está disponível
if command -v uv &> /dev/null; then
    echo "[INFO] uv detected! Using uv (much faster) / uv detectado! Usando uv (muito mais rápido)..."
    
    echo ""
    echo "[INFO] Creating virtual environment .venv with uv / Criando ambiente virtual .venv com uv..."
    uv venv
    
    echo "[ OK ] Virtual environment created! / Ambiente virtual criado!"
    echo ""
    echo "[INFO] Installing dependencies with uv / Instalando dependências com uv..."
    source .venv/bin/activate
    uv pip install --upgrade pip
    uv pip install -r requirements.txt
    
    echo ""
    echo "[ OK ] Setup completed successfully using uv! / Setup concluído com sucesso usando uv!"
    echo ""
    echo "To activate the virtual environment, run / Para ativar o ambiente virtual, execute:"
    echo "  source .venv/bin/activate"
    echo ""
    echo "Or use uv run (without activating) / Ou use uv run (sem precisar ativar):"
    echo "  uv run python -m cli.main --help"
    echo ""
    echo "To install project in development mode / Para instalar o projeto em modo desenvolvimento:"
    echo "  uv pip install -e ."
    echo ""
    echo "Useful uv commands / Comandos úteis com uv:"
    echo "  uv pip install <package>     # Install package / Instalar pacote"
    echo "  uv pip list                  # List packages / Listar pacotes"
    echo "  uv run <command>             # Run in virtual environment / Executar no ambiente virtual"
    
else
    echo "[INFO] uv not found. Using traditional venv / uv não encontrado. Usando venv tradicional..."
    
    echo ""
    echo "[INFO] Creating virtual environment .venv / Criando ambiente virtual .venv..."
    $PYTHON_CMD -m venv .venv
    
    echo "[ OK ] Virtual environment created! / Ambiente virtual criado!"
    echo ""
    echo "[INFO] Installing dependencies / Instalando dependências..."
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo ""
    echo "[ OK ] Setup completed successfully! / Setup concluído com sucesso!"
    echo ""
    echo "Tip: Install uv for faster setup next time / Dica: Instale uv para setup mais rápido na próxima vez:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "To activate the virtual environment, run / Para ativar o ambiente virtual, execute:"
    echo "  source .venv/bin/activate"
    echo ""
    echo "Or from Windows WSL / Ou no WSL a partir do Windows:"
    echo "  wsl bash -c 'cd $PROJECT_DIR && source .venv/bin/activate && bash'"
    echo ""
    echo "To install project in development mode / Para instalar o projeto em modo desenvolvimento:"
    echo "  pip install -e ."
fi
