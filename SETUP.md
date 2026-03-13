# Virtual Environment Setup

> **Language Navigation / Navegação**
> - [English Version](#english-version)
> - [Versão em Português](#versao-em-portugues)

---

## English Version

This guide helps you set up the Python virtual environment across different platforms (WSL, Windows, macOS, Linux).

### 🚨 Common Issue

If you receive this error:

```
The virtual environment was not created successfully because ensurepip is not available.
On Debian/Ubuntu systems, you need to install the python3-venv package
```

This means the `python3-venv` package is not installed **OR** you're using pyenv and need to ensure Python is installed correctly.

---

### Quick Solution

#### Option 1: Using uv + pyenv (Recommended)

`uv` is an extremely fast Python package manager developed by Astral (creators of Ruff). It replaces pip and venv with superior performance.

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip (if you already have Python)
pip install uv

# 2. Check available Python version via pyenv
pyenv versions

# 3. Install Python 3.11 if not installed
pyenv install 3.11.14

# 4. Set local project version (creates .python-version)
pyenv local 3.11.14

# 5. Verify correct version
python --version # Should show Python 3.11.x

# 6. Create .venv with uv (much faster than venv)
uv venv

# 7. Activate virtual environment
source .venv/bin/activate

# 8. Install dependencies with uv (much faster than pip)
uv pip install -r requirements.txt

# 9. (Optional) Install project in dev mode
uv pip install -e .

# Alternative: Use uv sync (if you have pyproject.toml)
# uv sync
```

**uv advantages:**
- **10-100x faster** than pip
- **More secure** (better dependency resolution)
- **Integrated environment management**
- **Compatible** with pip and requirements.txt

---

#### Option 2: Using pyenv (Traditional)

```bash
# 1. Check available Python version
pyenv versions

# 2. Install Python 3.11 if not installed
pyenv install 3.11.14

# 3. Set local project version (creates .python-version)
pyenv local 3.11.14

# 4. Verify correct version
python --version # Should show Python 3.11.x

# 5. Create .venv (with pyenv, venv is included)
python -m venv .venv

# 6. Activate virtual environment
source .venv/bin/activate

# 7. Upgrade pip
pip install --upgrade pip

# 8. Install dependencies
pip install -r requirements.txt

# 9. (Optional) Install project in dev mode
pip install -e .
```

#### Option 3: Automated Scripts (Bash, PowerShell, Zsh)

| Shell / OS | Script / Command | Notes |
|---|---|---|
| **WSL / Linux (bash)** | `wsl bash setup_venv.sh` or `./setup_venv.sh` | Original Bash script for WSL provisioning. |
| **PowerShell (Windows / PS7)** | `pwsh -File .\setup_venv.ps1` Parameters: `-ProjectPath`, `-Force`, `-SkipUv` | Ensures Python 3.11+, prefers `uv`, recreates `.venv` when `-Force`. |
| **Zsh (macOS / Linux / WSL)** | `./setup_venv.zsh` (or `zsh setup_venv.zsh`) | Compatible with macOS/WSL, detects `pyenv`/`uv`, installs deps automatically. |

> All scripts:
> - Detect `pyenv`, `uv`, and Python 3.11+ automatically.
> - Install dependencies from `requirements.txt`.
> - Print how to activate `.venv` and run `uv run ...`.

#### Option 4: Manual Setup (without pyenv)

```bash
# 1. Install python3-venv
sudo apt-get update
sudo apt-get install -y python3.11-venv python3-pip

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Upgrade pip
pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. (Optional) Install project in development mode
pip install -e .
```

---

### 🔄 Activating the Virtual Environment

#### In WSL (inside WSL terminal)

```bash
cd /mnt/c/Users/benjamin.rebello/Documents/projetos/prototipos/ref/context-engineer
source .venv/bin/activate
```

#### From Windows PowerShell (running WSL commands)

```powershell
wsl bash -c "cd /mnt/c/Users/benjamin.rebello/Documents/projetos/prototipos/ref/context-engineer && source .venv/bin/activate && bash"
```

#### From Windows PowerShell (running specific command)

```powershell
wsl bash -c "cd /mnt/c/Users/benjamin.rebello/Documents/projetos/prototipos/ref/context-engineer && source .venv/bin/activate && python -m cli.main --help"
```

---

### Useful uv Commands

#### Installation and Management

```bash
# Create virtual environment
uv venv

# Install dependencies from requirements.txt
uv pip install -r requirements.txt

# Install a specific dependency
uv pip install package-name

# Upgrade all dependencies
uv pip install --upgrade -r requirements.txt

# List installed packages
uv pip list

# Uninstall package
uv pip uninstall package-name

# Install project in dev mode
uv pip install -e .
```

#### Working with pyproject.toml (Recommended)

If you create a `pyproject.toml`, you can use advanced commands:

```bash
# Add dependency (updates pyproject.toml automatically)
uv add package-name

# Add development dependency
uv add --dev pytest

# Remove dependency
uv remove package-name

# Sync environment with pyproject.toml
uv sync

# Update all dependencies
uv sync --upgrade
```

#### Running Commands in Virtual Environment

```bash
# Run Python command in virtual environment (without activating)
uv run python script.py

# Run CLI command installed in virtual environment
uv run ce --help

# Run pytest
uv run pytest
```

---

### 🧪 Verify Installation

```bash
# Activate venv
source .venv/bin/activate

# Check Python
python --version # Should show Python 3.11.x

# Check pip
pip --version

# List installed packages
pip list

# Test CLI (if installed)
ce --help
# or
python -m cli.main --help
```

---

### 🤖 LLM Provider Configuration

Context Engineer supports multiple LLM providers (API and local). After setting up the environment, configure your preferred provider and model.

#### Step 1 — Configure a Provider

```bash
# Interactive setup (recommended)
ce provider setup

# Or specify directly
ce provider setup --provider-id openai
ce provider setup --provider-id local-ollama
```

#### Step 2 — Set API Key (API providers only)

```bash
# Store API key securely (encrypted)
ce provider set-key openai
ce provider set-key gemini
ce provider set-key anthropic
```

API keys are encrypted and stored locally in `~/.config/context-engineer/`. You can also use environment variables:

| Provider | Environment Variable |
|---|---|
| OpenAI | `OPENAI_API_KEY` |
| Gemini | `GEMINI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| GROQ | `GROQ_API_KEY` |
| xAI (Grok) | `XAI_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |

#### Step 3 — Custom Model Selection

You can use any model available in your provider's API. The model name **must match exactly** what the provider's API expects. Check the provider's documentation for available model identifiers.

```bash
# Set a custom model
ce provider set-model openai gpt-4-turbo
ce provider set-model gemini gemini-1.5-pro
ce provider set-model anthropic claude-opus-4-20250514
ce provider set-model local-ollama codellama:13b
ce provider set-model deepseek deepseek-reasoner

# View current configuration
ce provider show

# List all providers and default models
ce provider list
```

> When using `ce provider show`, custom models are indicated with a `(custom)` label.

#### Local Providers

For local providers (Ollama, LM Studio), no API key is required. You can configure a custom port and model:

```bash
# Ollama with custom model and port
ce provider setup --provider-id local-ollama --model codellama:13b --port 11434

# LM Studio
ce provider setup --provider-id local-lm-studio --model my-local-model --port 1234
```

---

### 🐛 Troubleshooting

#### Error with uv: "uv: command not found"

If uv is not installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv

# Reload shell
source ~/.bashrc # or source ~/.zshrc

# Verify installation
uv --version
```

#### Error with uv: "Python version not found"

uv needs to find Python. With pyenv:
```bash
# Ensure pyenv is configured
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Set local version
pyenv local 3.11.14

# Verify Python is available
python --version

# Create venv with uv specifying Python
uv venv --python 3.11.14
```

#### Error with pyenv: "pyenv: command not found"

If pyenv is not configured in your shell:
```bash
# Add to ~/.bashrc or ~/.zshrc
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Reload shell
source ~/.bashrc # or source ~/.zshrc

# Verify installation
pyenv --version
```

#### Error with pyenv: "python: command not found" after pyenv install

If Python is not found after installing via pyenv:
```bash
pyenv version
pyenv rehash
which python
python --version # Should show Python 3.11.x

# If not using 3.11, set locally
pyenv local 3.11.14
```

#### Error with pyenv: "ensurepip is not available"

With pyenv, you need to install Python with venv support. Make sure build dependencies are installed:
```bash
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
 libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
 libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev

# Reinstall Python 3.11 via pyenv
pyenv install 3.11.14
pyenv local 3.11.14
pyenv rehash
```

#### Error: "sudo: command not found"

If sudo is not configured in WSL:
```bash
su -
apt-get install -y python3.11-venv python3-pip
```

#### Error: "python3-venv package not found"

Check your Python version and install the matching venv package:
```bash
python3 --version
# If 3.12, use: python3.12-venv
# If 3.11, use: python3.11-venv
# If 3.10, use: python3.10-venv
```

#### Error: "Permission denied" when activating venv

```bash
ls -la .venv/bin/activate
chmod +x .venv/bin/activate
```

#### Windows/WSL path issues

The project is at `/mnt/c/...` which is the WSL path for `C:\...` on Windows.
- **WSL**: Use `/mnt/c/Users/...`
- **Windows**: Use `C:\Users\...`

---

### Important Notes

1. **Always activate venv** before running Python commands (or use `uv run`)
2. **Use `source .venv/bin/activate`** in WSL (not `.venv\Scripts\activate` from Windows)
3. **WSL venv is specific** — doesn't work directly in Windows PowerShell
4. **To use on Windows**, you'd need to create a separate venv using Windows Python
5. **With pyenv**: The `.python-version` file defines the Python version for this project (3.11.14)
6. **With pyenv**: Run `pyenv local 3.11.14` to set the local project version
7. **This project uses Python 3.11** via pyenv and creates the virtual environment in `.venv`
8. **Recommended to use `uv`**: Much faster than traditional pip/venv and fully compatible
9. **With uv**: You can use `uv run <command>` without manually activating venv
10. **uv works perfectly with pyenv**: Just need Python configured via pyenv

---

### 🔗 Next Steps

After setting up the environment:

1. Read [README.md](README.md) to understand the project
2. Configure your LLM provider: `ce provider setup`
3. Check [MAIN_USAGE_GUIDE.md](docs/MAIN_USAGE_GUIDE.md) to get started
4. See [docs/CLI_COMMANDS.md](docs/CLI_COMMANDS.md) for the full CLI reference

---

## Versão em Português

Este guia ajuda a configurar o ambiente virtual Python em diferentes plataformas (WSL, Windows, macOS, Linux).

### 🚨 Problema Comum

Se você receber este erro:

```
The virtual environment was not created successfully because ensurepip is not available.
On Debian/Ubuntu systems, you need to install the python3-venv package
```

Isso significa que o pacote `python3-venv` não está instalado **OU** você está usando pyenv e precisa garantir que o Python está instalado corretamente.

---

### Solução Rápida

#### Opção 1: Usando uv + pyenv (Recomendado)

`uv` é um gerenciador de pacotes Python extremamente rápido desenvolvido pela Astral (criadores do Ruff). Ele substitui pip e venv com performance muito superior.

```bash
# 1. Instalar uv (se ainda não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ou via pip (se já tiver Python)
pip install uv

# 2. Verificar versão do Python disponível via pyenv
pyenv versions

# 3. Instalar Python 3.11 se não estiver instalado
pyenv install 3.11.14

# 4. Definir versão local do projeto (cria .python-version)
pyenv local 3.11.14

# 5. Verificar que está usando a versão correta
python --version # Deve mostrar Python 3.11.x

# 6. Criar ambiente virtual .venv com uv (muito mais rápido que venv)
uv venv

# 7. Ativar ambiente virtual
source .venv/bin/activate

# 8. Instalar dependências com uv (muito mais rápido que pip)
uv pip install -r requirements.txt

# 9. (Opcional) Instalar projeto em modo desenvolvimento
uv pip install -e .

# Alternativa: Usar uv sync (se tiver pyproject.toml)
# uv sync
```

**Vantagens do uv:**
- **10-100x mais rápido** que pip
- **Mais seguro** (melhor resolução de dependências)
- **Gerenciamento de ambientes** integrado
- **Compatível** com pip e requirements.txt

---

#### Opção 2: Usando pyenv (Tradicional)

```bash
# 1. Verificar versão do Python disponível
pyenv versions

# 2. Instalar Python 3.11 se não estiver instalado
pyenv install 3.11.14

# 3. Definir versão local do projeto (cria .python-version)
pyenv local 3.11.14

# 4. Verificar que está usando a versão correta
python --version # Deve mostrar Python 3.11.x

# 5. Criar ambiente virtual .venv (com pyenv, venv já vem incluído)
python -m venv .venv

# 6. Ativar ambiente virtual
source .venv/bin/activate

# 7. Atualizar pip
pip install --upgrade pip

# 8. Instalar dependências
pip install -r requirements.txt

# 9. (Opcional) Instalar projeto em modo desenvolvimento
pip install -e .
```

#### Opção 3: Scripts Automatizados (Bash, PowerShell, Zsh)

| Shell / SO | Script / Comando | Observações |
|---|---|---|
| **WSL / Linux (bash)** | `wsl bash setup_venv.sh` ou `./setup_venv.sh` | Script original (Bash) para provisionar via WSL. |
| **PowerShell (Windows / PS7)** | `pwsh -File .\setup_venv.ps1` Parâmetros: `-ProjectPath`, `-Force`, `-SkipUv` | Garante Python 3.11+, prefere `uv`, recria `.venv` com `-Force`. |
| **Zsh (macOS / Linux / WSL)** | `./setup_venv.zsh` (ou `zsh setup_venv.zsh`) | Compatível com macOS/WSL, detecta `pyenv`/`uv`, instala dependências automaticamente. |

> Todos os scripts:
> - Detectam `pyenv`, `uv` e Python 3.11+ automaticamente.
> - Instalam dependências do `requirements.txt`.
> - Mostram como ativar o `.venv` e rodar `uv run ...`.

#### Opção 4: Setup Manual (sem pyenv)

```bash
# 1. Instalar python3-venv
sudo apt-get update
sudo apt-get install -y python3.11-venv python3-pip

# 2. Criar ambiente virtual
python3 -m venv .venv

# 3. Ativar ambiente virtual
source .venv/bin/activate

# 4. Atualizar pip
pip install --upgrade pip

# 5. Instalar dependências
pip install -r requirements.txt

# 6. (Opcional) Instalar projeto em modo desenvolvimento
pip install -e .
```

---

### 🔄 Ativando o Ambiente Virtual

#### No WSL (dentro do terminal WSL)

```bash
cd /mnt/c/Users/benjamin.rebello/Documents/projetos/prototipos/ref/context-engineer
source .venv/bin/activate
```

#### Do Windows PowerShell (executando comandos no WSL)

```powershell
wsl bash -c "cd /mnt/c/Users/benjamin.rebello/Documents/projetos/prototipos/ref/context-engineer && source .venv/bin/activate && bash"
```

#### Do Windows PowerShell (executando comando específico)

```powershell
wsl bash -c "cd /mnt/c/Users/benjamin.rebello/Documents/projetos/prototipos/ref/context-engineer && source .venv/bin/activate && python -m cli.main --help"
```

---

### Comandos Úteis com uv

#### Instalação e Gerenciamento

```bash
# Criar ambiente virtual
uv venv

# Instalar dependências do requirements.txt
uv pip install -r requirements.txt

# Instalar uma dependência específica
uv pip install nome-do-pacote

# Atualizar todas as dependências
uv pip install --upgrade -r requirements.txt

# Listar pacotes instalados
uv pip list

# Desinstalar pacote
uv pip uninstall nome-do-pacote

# Instalar projeto em modo desenvolvimento
uv pip install -e .
```

#### Trabalhando com pyproject.toml (Recomendado)

Se você criar um `pyproject.toml`, pode usar comandos mais avançados:

```bash
# Adicionar dependência (atualiza pyproject.toml automaticamente)
uv add nome-do-pacote

# Adicionar dependência de desenvolvimento
uv add --dev pytest

# Remover dependência
uv remove nome-do-pacote

# Sincronizar ambiente com pyproject.toml
uv sync

# Atualizar todas as dependências
uv sync --upgrade
```

#### Executar Comandos no Ambiente Virtual

```bash
# Executar comando Python no ambiente virtual (sem ativar)
uv run python script.py

# Executar comando CLI instalado no ambiente virtual
uv run ce --help

# Executar pytest
uv run pytest
```

---

### 🧪 Verificar Instalação

```bash
# Ativar venv
source .venv/bin/activate

# Verificar Python
python --version # Deve mostrar Python 3.11.x

# Verificar pip
pip --version

# Verificar pacotes instalados
pip list

# Testar CLI (se instalado)
ce --help
# ou
python -m cli.main --help
```

---

### 🤖 Configuração do Provedor LLM

O Context Engineer suporta múltiplos provedores LLM (API e local). Após configurar o ambiente, configure seu provedor e modelo preferido.

#### Passo 1 — Configurar um Provedor

```bash
# Setup interativo (recomendado)
ce provider setup

# Ou especifique diretamente
ce provider setup --provider-id openai
ce provider setup --provider-id local-ollama
```

#### Passo 2 — Definir API Key (apenas provedores API)

```bash
# Armazenar API key com segurança (criptografada)
ce provider set-key openai
ce provider set-key gemini
ce provider set-key anthropic
```

As API keys são criptografadas e armazenadas localmente em `~/.config/context-engineer/`. Você também pode usar variáveis de ambiente:

| Provedor | Variável de Ambiente |
|---|---|
| OpenAI | `OPENAI_API_KEY` |
| Gemini | `GEMINI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| GROQ | `GROQ_API_KEY` |
| xAI (Grok) | `XAI_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |

#### Passo 3 — Seleção de Modelo Customizado

Você pode usar qualquer modelo disponível na API do seu provedor. O nome do modelo **deve ser idêntico** ao que a API do provedor espera. Consulte a documentação do provedor para identificadores de modelos disponíveis.

```bash
# Definir um modelo customizado
ce provider set-model openai gpt-4-turbo
ce provider set-model gemini gemini-1.5-pro
ce provider set-model anthropic claude-opus-4-20250514
ce provider set-model local-ollama codellama:13b
ce provider set-model deepseek deepseek-reasoner

# Ver configuração atual
ce provider show

# Listar provedores e modelos padrão
ce provider list
```

> Ao usar `ce provider show`, modelos customizados são indicados com o rótulo `(custom)`.

#### Provedores Locais

Para provedores locais (Ollama, LM Studio), não é necessária API key. Você pode configurar porta e modelo customizados:

```bash
# Ollama com modelo e porta customizados
ce provider setup --provider-id local-ollama --model codellama:13b --port 11434

# LM Studio
ce provider setup --provider-id local-lm-studio --model my-local-model --port 1234
```

---

### 🐛 Solução de Problemas

#### Erro com uv: "uv: command not found"

Se o uv não estiver instalado:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ou via pip
pip install uv

# Recarregar shell
source ~/.bashrc # ou source ~/.zshrc

# Verificar instalação
uv --version
```

#### Erro com uv: "Python version not found"

O uv precisa encontrar o Python. Com pyenv:
```bash
# Garantir que pyenv está configurado
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Definir versão local
pyenv local 3.11.14

# Verificar que Python está disponível
python --version

# Criar venv com uv especificando Python
uv venv --python 3.11.14
```

#### Erro com pyenv: "pyenv: command not found"

Se o pyenv não estiver configurado no seu shell:
```bash
# Adicionar ao ~/.bashrc ou ~/.zshrc
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Recarregar shell
source ~/.bashrc # ou source ~/.zshrc

# Verificar instalação
pyenv --version
```

#### Erro com pyenv: "python: command not found" após pyenv install

Se o Python não for encontrado após instalar via pyenv:
```bash
pyenv version
pyenv rehash
which python
python --version # Deve mostrar Python 3.11.x

# Se não estiver usando 3.11, definir localmente
pyenv local 3.11.14
```

#### Erro com pyenv: "ensurepip is not available"

Com pyenv, você precisa instalar o Python com suporte a venv. Certifique-se de ter as dependências de build instaladas:
```bash
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
 libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
 libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev

# Reinstalar Python 3.11 via pyenv
pyenv install 3.11.14
pyenv local 3.11.14
pyenv rehash
```

#### Erro: "sudo: command not found"

Se você não tem sudo configurado no WSL:
```bash
su -
apt-get install -y python3.11-venv python3-pip
```

#### Erro: "python3-venv package not found"

Verifique a versão do Python e instale o pacote venv correspondente:
```bash
python3 --version
# Se for 3.12, use: python3.12-venv
# Se for 3.11, use: python3.11-venv
# Se for 3.10, use: python3.10-venv
```

#### Erro: "Permission denied" ao ativar venv

```bash
ls -la .venv/bin/activate
chmod +x .venv/bin/activate
```

#### Problemas com caminhos Windows/WSL

O projeto está em `/mnt/c/...` que é o caminho WSL para `C:\...` no Windows.
- **WSL**: Use `/mnt/c/Users/...`
- **Windows**: Use `C:\Users\...`

---

### Notas Importantes

1. **Sempre ative o venv** antes de executar comandos Python (ou use `uv run`)
2. **Use `source .venv/bin/activate`** no WSL (não `.venv\Scripts\activate` do Windows)
3. **O venv é específico do WSL** — não funciona diretamente no PowerShell do Windows
4. **Para usar no Windows**, você precisaria criar um venv separado usando Python do Windows
5. **Com pyenv**: O arquivo `.python-version` define a versão do Python para este projeto (3.11.14)
6. **Com pyenv**: Execute `pyenv local 3.11.14` para definir a versão local do projeto
7. **Este projeto usa Python 3.11** via pyenv e cria o ambiente virtual em `.venv`
8. **Recomendado usar `uv`**: É muito mais rápido que pip/venv tradicional e totalmente compatível
9. **Com uv**: Você pode usar `uv run <comando>` sem precisar ativar o venv manualmente
10. **uv funciona perfeitamente com pyenv**: Basta ter o Python configurado via pyenv

---

### 🔗 Próximos Passos

Após configurar o ambiente:

1. Leia o [README.md](README.md) para entender o projeto
2. Configure seu provedor LLM: `ce provider setup`
3. Consulte [MAIN_USAGE_GUIDE.md](docs/MAIN_USAGE_GUIDE.md) para começar
4. Veja [docs/CLI_COMMANDS.md](docs/CLI_COMMANDS.md) para referência completa do CLI
