# Virtual Environment Setup / Configuração do Ambiente Virtual

**EN:** This guide helps you set up the Python virtual environment across different platforms (WSL, Windows, macOS, Linux).  
**PT:** Este guia ajuda a configurar o ambiente virtual Python em diferentes plataformas (WSL, Windows, macOS, Linux).

---

## 🚨 Common Issue / Problema Comum

**EN:** If you receive this error:  
**PT:** Se você receber este erro:

```
The virtual environment was not created successfully because ensurepip is not available.
On Debian/Ubuntu systems, you need to install the python3-venv package
```

**EN:** This means the `python3-venv` package is not installed **OR** you're using pyenv and need to ensure Python is installed correctly.  
**PT:** Isso significa que o pacote `python3-venv` não está instalado **OU** você está usando pyenv e precisa garantir que o Python está instalado corretamente.

---

## Quick Solution / Solução Rápida

### Option 1 / Opção 1: Using uv + pyenv (Recommended / Recomendado)

**EN:** `uv` is an extremely fast Python package manager developed by Astral (creators of Ruff). It replaces pip and venv with superior performance.  
**PT:** `uv` é um gerenciador de pacotes Python extremamente rápido desenvolvido pela Astral (criadores do Ruff). Ele substitui pip e venv com performance muito superior.

```bash
# 1. Instalar uv (se ainda não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ou via pip (se já tiver Python)
pip install uv

# 2. Verificar versão do Python disponível via pyenv
pyenv versions

# 3. Instalar Python 3.11 se não estiver instalado
pyenv install 3.11.14 # ou use a versão 3.11.x que você já tem instalada

# 4. Definir versão local do projeto (cria .python-version)
pyenv local 3.11.14 # ou a versão 3.11.x que você tem instalada

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

**EN - uv advantages:** · **PT - Vantagens do uv:**
- **10-100x faster** than pip · **10-100x mais rápido** que pip
- **More secure** (better dependency resolution) · **Mais seguro** (resolver de dependências melhor)
- **Integrated environment management** · **Gerenciamento de ambientes** integrado
- 🔄 **Compatible** with pip and requirements.txt · **Compatível** com pip e requirements.txt

---

### Option 2 / Opção 2: Using pyenv (Traditional / Tradicional)

```bash
# 1. Verificar versão do Python disponível
pyenv versions

# 2. Instalar Python 3.11 se não estiver instalado (ou usar versão já instalada)
# Verifique versões disponíveis: pyenv versions
pyenv install 3.11.14 # ou use a versão 3.11.x que você já tem instalada

# 3. Definir versão local do projeto (cria .python-version)
pyenv local 3.11.14 # ou a versão 3.11.x que você tem instalada

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

### Option 3 — Automated Scripts / Scripts Automatizados (Bash, PowerShell, Zsh)

| Shell / OS (EN) · Shell / SO (PT) | Script / Command · Script / Comando                                                                                 | Notes (EN) · Observações (PT) |
|----------------------------------|----------------------------------------------------------------------------------------------------------------------|--------------------------------|
| **WSL / Linux (bash)**           | `wsl bash setup_venv.sh` or `./setup_venv.sh`                                                                        | Original Bash script for WSL provisioning · Script original (Bash) para provisionar via WSL. |
| **PowerShell (Windows / PS7)**   | `pwsh -File .\setup_venv.ps1` <br/>Parameters/Parâmetros: `-ProjectPath`, `-Force`, `-SkipUv`                        | Ensures Python 3.11+, prefers `uv`, recreates `.venv` when `-Force` · Garante Python 3.11+, prefere `uv`, recria `.venv` com `-Force`. |
| **Zsh (macOS / Linux / WSL)**    | `./setup_venv.zsh` (or `zsh setup_venv.zsh`)                                                                         | Compatible with macOS/WSL, detects `pyenv`/`uv`, installs deps automatically · Compatível com macOS/WSL, detecta `pyenv`/`uv`, instala dependências automaticamente. |

> All scripts / Todos os scripts:
> - Detect `pyenv`, `uv`, and Python 3.11+ automatically · Detectam `pyenv`, `uv` e Python 3.11+ automaticamente.
> - Install dependencies from `requirements.txt` · Instalam dependências do `requirements.txt`.
> - Print how to activate `.venv` and run `uv run ...` · Mostram como ativar o `.venv` e rodar `uv run ...`.

### Option 4 / Opção 4: Manual Setup (without pyenv / sem pyenv)

```bash
# 1. Install python3-venv / Instalar python3-venv
sudo apt-get update
sudo apt-get install -y python3.11-venv python3-pip

# 2. Create virtual environment / Criar ambiente virtual
python3 -m venv .venv

# 3. Activate virtual environment / Ativar ambiente virtual
source .venv/bin/activate

# 4. Upgrade pip / Atualizar pip
pip install --upgrade pip

# 5. Install dependencies / Instalar dependências
pip install -r requirements.txt

# 6. (Optional) Install project in development mode / (Opcional) Instalar projeto em modo desenvolvimento
pip install -e .
```

---

## 🔄 Activating the Virtual Environment / Ativando o Ambiente Virtual

### In WSL (inside WSL terminal) / No WSL (dentro do terminal WSL)

```bash
cd /mnt/c/Users/benjamin.rebello/Documents/projetos/prototipos/ref/context-engineer
source .venv/bin/activate
```

### From Windows PowerShell (running WSL commands) / Do Windows PowerShell (executando comandos no WSL)

```powershell
wsl bash -c "cd /mnt/c/Users/benjamin.rebello/Documents/projetos/prototipos/ref/context-engineer && source .venv/bin/activate && bash"
```

### From Windows PowerShell (running specific command) / Do Windows PowerShell (executando comando específico)

```powershell
wsl bash -c "cd /mnt/c/Users/benjamin.rebello/Documents/projetos/prototipos/ref/context-engineer && source .venv/bin/activate && python -m cli.main --help"
```

---

## Useful uv Commands / Comandos Úteis com uv

### Installation and Management / Instalação e Gerenciamento

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

### Working with pyproject.toml (Recommended) / Trabalhando com pyproject.toml (Recomendado)

**EN:** If you create a `pyproject.toml`, you can use advanced commands:  
**PT:** Se você criar um `pyproject.toml`, pode usar comandos mais avançados:

```bash
# Add dependency (updates pyproject.toml automatically) / Adicionar dependência (atualiza pyproject.toml automaticamente)
uv add nome-do-pacote

# Add development dependency / Adicionar dependência de desenvolvimento
uv add --dev pytest

# Remove dependency / Remover dependência
uv remove nome-do-pacote

# Sync environment with pyproject.toml / Sincronizar ambiente com pyproject.toml
uv sync

# Update all dependencies / Atualizar todas as dependências
uv sync --upgrade
```

### Running Commands in Virtual Environment / Executar Comandos no Ambiente Virtual

```bash
# Run Python command in virtual environment (without activating) / Executar comando Python no ambiente virtual (sem ativar)
uv run python script.py

# Run CLI command installed in virtual environment / Executar comando CLI instalado no ambiente virtual
uv run ce --help

# Run pytest / Executar pytest
uv run pytest
```

---

## 🧪 Verify Installation / Verificar Instalação

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

## 🐛 Troubleshooting / Solução de Problemas

### Error with uv: "uv: command not found" / Erro com uv: "uv: command not found"

**EN:** If uv is not installed:  
**PT:** Se o uv não estiver instalado:
```bash
# Instalar uv via script oficial
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ou via pip (se já tiver Python)
pip install uv

# Recarregar shell
source ~/.bashrc # ou source ~/.zshrc

# Verificar instalação
uv --version
```

### Error with uv: "Python version not found" / Erro com uv: "Python version not found"

**EN:** uv needs to find Python. With pyenv:  
**PT:** O uv precisa encontrar o Python. Com pyenv:
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

### Error with pyenv: "pyenv: command not found" / Erro com pyenv: "pyenv: command not found"

**EN:** If pyenv is not configured in your shell:  
**PT:** Se o pyenv não estiver configurado no seu shell:
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

### Erro com pyenv: "python: command not found" após pyenv install
```bash
# Verificar se pyenv está ativo
pyenv version

# Rehash pyenv (atualiza shims)
pyenv rehash

# Verificar qual Python está sendo usado
which python
python --version # Deve mostrar Python 3.11.x

# Se não estiver usando 3.11, definir localmente
pyenv local 3.11.14 # ou a versão 3.11.x que você tem instalada
```

### Erro com pyenv: "ensurepip is not available" com pyenv
```bash
# Com pyenv, você precisa instalar o Python com suporte a venv
# Certifique-se de ter as dependências de build instaladas
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
 libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
 libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev

# Reinstalar Python 3.11 via pyenv
pyenv install 3.11.14
pyenv local 3.11.14
pyenv rehash
```

### Erro: "sudo: command not found"
Se você não tem sudo configurado no WSL:
```bash
# Configure sudo ou use como root
su -
apt-get install -y python3.11-venv python3-pip
```

### Erro: "python3-venv package not found"
Verifique a versão do Python:
```bash
python3 --version
# Se for 3.12, use: python3.12-venv
# Se for 3.11, use: python3.11-venv
# Se for 3.10, use: python3.10-venv
```

### Erro: "Permission denied" ao ativar venv
```bash
# Verificar permissões
ls -la .venv/bin/activate

# Corrigir permissões se necessário
chmod +x .venv/bin/activate
```

### Problemas com caminhos Windows/WSL
O projeto está em `/mnt/c/...` que é o caminho WSL para `C:\...` no Windows.
- **WSL**: Use `/mnt/c/Users/...`
- **Windows**: Use `C:\Users\...`

## Important Notes / Notas Importantes

**EN:**
1. **Always activate venv** before running Python commands (or use `uv run`)
2. **Use `source .venv/bin/activate`** in WSL (not `.venv\Scripts\activate` from Windows)
3. **WSL venv is specific** - doesn't work directly in Windows PowerShell
4. **To use on Windows**, you'd need to create a separate venv using Windows Python
5. **With pyenv**: The `.python-version` file defines the Python version for this project (3.11.14)
6. **With pyenv**: Run `pyenv local 3.11.14` to set the local project version
7. **This project uses Python 3.11** via pyenv and creates the virtual environment in `.venv`
8. **Recommended to use `uv`**: Much faster than traditional pip/venv and fully compatible
9. **With uv**: You can use `uv run <command>` without manually activating venv
10. **uv works perfectly with pyenv**: Just need Python configured via pyenv

**PT:**
1. **Sempre ative o venv** antes de executar comandos Python (ou use `uv run`)
2. **Use `source .venv/bin/activate`** no WSL (não `.venv\Scripts\activate` do Windows)
3. **O venv é específico do WSL** - não funciona diretamente no PowerShell do Windows
4. **Para usar no Windows**, você precisaria criar um venv separado usando Python do Windows
5. **Com pyenv**: O arquivo `.python-version` define a versão do Python para este projeto (3.11.14)
6. **Com pyenv**: Execute `pyenv local 3.11.14` para definir a versão local do projeto
7. **Este projeto usa Python 3.11** via pyenv e cria o ambiente virtual em `.venv`
8. **Recomendado usar `uv`**: É muito mais rápido que pip/venv tradicional e totalmente compatível
9. **Com uv**: Você pode usar `uv run <comando>` sem precisar ativar o venv manualmente
10. **uv funciona perfeitamente com pyenv**: Basta ter o Python configurado via pyenv

---

## 🔗 Next Steps / Próximos Passos

**EN:** After setting up the environment:  
**PT:** Após configurar o ambiente:

1. Read [README.md](README.md) to understand the project / Leia o [README.md](README.md) para entender o projeto
2. Check [MAIN_USAGE_GUIDE.md](docs/MAIN_USAGE_GUIDE.md) to get started / Consulte [MAIN_USAGE_GUIDE.md](docs/MAIN_USAGE_GUIDE.md) para começar
3. See [docs/analise/USO_CLI.md](docs/analise/USO_CLI.md) to use the CLI / Veja [docs/analise/USO_CLI.md](docs/analise/USO_CLI.md) para usar o CLI
