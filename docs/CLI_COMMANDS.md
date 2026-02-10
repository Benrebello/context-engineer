# Context Engineer - CLI Commands Manual / Manual de Comandos CLI

> **Language Navigation / Navegação de Idioma**
> 1. [English Version](#english-version)
> 2. [Versão em Português](#versao-em-portugues)

---

## English Version

### Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Generation Commands](#generation-commands)
- [Validation Commands](#validation-commands)
- [AI Governance Commands](#ai-governance-commands)
- [DevOps Commands](#devops-commands)
- [Marketplace Commands](#marketplace-commands)
- [Provider Commands](#provider-commands)
- [Status & Reporting Commands](#status--reporting-commands)
- [Utility Commands](#utility-commands)
- [Intelligence Modes](#intelligence-modes)
- [Per-Project Configuration](#per-project-configuration)
- [Usage Examples](#usage-examples)

---

### Overview

Context Engineer is a CLI framework for context engineering and AI governance in software projects. It provides tools for:

- Automated generation of PRD, PRPs and Tasks
- Contract and traceability validation
- AI governance and prompt optimization
- Project metrics and monitoring
- Git and CI/CD integration

**Base command:** `ce`

**General help:**
```bash
ce --help
```

**Specific command help:**
```bash
ce <command> --help
```

---

### Installation

#### Install via pip

```bash
pip install -e .
```

#### Install with AI dependencies

```bash
pip install -e ".[ai]"
```

#### Install for development

```bash
pip install -e ".[dev]"
```

#### Verify installation

```bash
ce --version
```

---

### Generation Commands

#### `ce init` - Initialize Project / Inicializar Projeto

Creates the initial structure of a Context Engineer project with templates, scaffolding and Git hooks (`cli/commands/generation.py`, `core/engine.py`). / Cria a estrutura inicial de um projeto Context Engineer com templates, scaffolding e hooks Git.

**Syntax / Sintaxe:**
```bash
ce init [PROJECT_NAME] [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `PROJECT_NAME` | Project name (optional, uses folder name if omitted). / Nome do projeto. | folder name |
| `--template TEXT` | Template to apply. / Template a aplicar. | `base` |
| `--stack TEXT` | Technology stack (`python-fastapi`, `node-react`, `go-gin`, `vue3`). / Stack tecnológica. | `python-fastapi` |
| `--output PATH` | Output directory. / Diretório de saída. | `./` |
| `--git-hooks` | Generate Git hooks for automatic validation. / Gerar hooks Git. | `true` |
| `--language TEXT` | Project language (`en-us` or `pt-br`). / Idioma do projeto. | `en-us` |
| `--ai/--no-ai` | Intelligence mode. / Modo de inteligência. | prompt |
| `--embedding-model TEXT` | Embedding model for AI. / Modelo de embedding. | `all-minilm-l6-v2` |

**Examples / Exemplos:**
```bash
# Initialize Python FastAPI project
ce init my-api --stack python-fastapi

# Initialize with AI enabled and Portuguese
ce init my-project --ai --language pt-br --embedding-model all-minilm-l6-v2

# Initialize Node.js + React
ce init my-app --stack node-react --output ./projects/my-app

# Initialize Go + Gin without Git hooks
ce init my-service --stack go-gin --git-hooks false
```

**Created Structure:**
- `.ce-config.json` - Project configuration
- `.ce-intelligence.db` - SQLite database for metrics and cache
- `prd/` - Product Requirements Documents directory
- `prps/` - Product Requirement Phases directory
- `tasks/` - Generated tasks directory
- `.git/hooks/` - Git hooks (if enabled)
- Stack-specific files and directories

**Code References / Referências de Código:**
- Implementation: `cli/commands/generation.py` (lines 39-148)
- Service: `core/engine.py` (`init_project`)

**Created structure:**
```
my-project/
├── .ce-config.json          # Project configuration
├── .ce-intelligence.db      # SQLite with cache and metrics
├── prd/                     # Product Requirements Documents
├── prp/                     # Product Requirement Phases
├── tasks/                   # Generated tasks
├── .git/hooks/              # Git hooks for validation
└── [stack-specific files]   # Stack-specific files
```

---

#### `ce generate-prd` - Generate PRD / Gerar PRD

Generates a Product Requirements Document from an idea or input file (`cli/commands/generation.py`, `core/engine.py`). / Gera um Documento de Requisitos de Produto a partir de uma ideia ou arquivo de entrada.

**Syntax / Sintaxe:**
```bash
ce generate-prd [INPUT_FILE] [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `INPUT_FILE` | Input file with product idea (optional). / Arquivo com ideia do produto. | interactive |
| `--output PATH` | Output directory. / Diretório de saída. | `./prd` |
| `--interactive / -i` | Interactive conversational mode. / Modo conversacional interativo. | `false` |
| `--auto-validate` | Auto-validate after generation. / Validar automaticamente. | `true` |
| `--preview` | Show preview without creating files. / Mostrar prévia sem criar arquivos. | `false` |
| `--ai/--no-ai` | Intelligence mode. / Modo de inteligência. | project default |
| `--embedding-model TEXT` | Embedding model. / Modelo de embedding. | per config |

**Examples / Exemplos:**
```bash
# Interactive mode
ce generate-prd --interactive

# From file
ce generate-prd idea.txt --output ./docs/prd

# With preview (no files created)
ce generate-prd idea.md --preview

# With AI-powered analysis
ce generate-prd --interactive --ai --embedding-model all-minilm-l6-v2

# From file without auto-validation
ce generate-prd product-vision.md --auto-validate false
```

**Generated Files:**
- `PRD.md` - Human-readable document
- `prd_structured.json` - Structured data for automation

**Code References / Referências de Código:**
- Implementation: `cli/commands/generation.py`
- Service: `core/engine.py` (`generate_prd`)

---

#### `ce generate-prps` - Generate PRPs / Gerar PRPs

Generates Product Requirement Plans from a structured PRD, respecting the same flow enforced by `cli/commands/generation.py`. / Gera PRPs a partir de um PRD estruturado, seguindo o fluxo de `cli/commands/generation.py`.

**Syntax / Sintaxe:**
```bash
ce generate-prps [PRD_FILE] [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `PRD_FILE` | Structured PRD (`prd/prd_structured.json`) to consume. / PRD estruturado a ser usado. | auto-detect |
| `--output PATH` | Target folder for PRPs. / Pasta destino dos PRPs. | `./prps` |
| `--parallel` | Generate phases concurrently (experimental). / Gera fases em paralelo. | `false` |
| `--interactive / -i` | Guides detection of the PRD and extra context. / Guia a detecção do PRD e contexto extra. | `false` |
| `--auto-validate/--no-auto-validate` | Run soft validation right after generation. / Executa validação ao final. | `true` |
| `--preview` | Shows which files would be created without writing them. / Apenas pré-visualização. | `false` |
| `--phase F?` | Restrict generation to a single phase (e.g., `F3`). | `None` |
| `--ai/--no-ai` | Toggles hybrid intelligence mode. | project default |
| `--embedding-model TEXT` | Embedding model alias or full name. / Modelo de embedding. | per config |

**Examples / Exemplos:**
```bash
# Generate every phase non-interactively
ce generate-prps prd/prd_structured.json --output ./prps

# Interactive mode + limited to APIs (F3)
ce generate-prps --interactive --phase F3 --output ./prps_f3

# Preview only (no files)
ce generate-prps --preview
```

---

#### `ce generate-tasks` - Generate Tasks / Gerar Tasks

Creates executable TASKs from PRPs or via interactive User Story mode (`cli/commands/generation.py`). / Cria TASKs executáveis a partir dos PRPs ou via User Story interativa.

**Syntax / Sintaxe:**
```bash
ce generate-tasks [PRPS_DIR] [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `PRPS_DIR` | (Optional) Folder containing PRPs. If omitted the CLI auto-detects `./prps`. / (Opcional) Pasta com PRPs. | auto-detect |
| `--output PATH` | Destination for generated TASKs. | `./tasks` |
| `--interactive / -i` | Guided prompts to locate PRPs when argument missing. | `false` |
| `--from-us` | Enables interactive User Story flow (bypasses PRPs). | `false` |
| `--ai/--no-ai` | Hybrid intelligence toggle. | project default |
| `--embedding-model TEXT` | Embedding alias or ID. | per config |

**Examples / Exemplos:**
```bash
# Standard generation from PRPs folder
ce generate-tasks ./prps --output ./tasks

# Ask for PRPs path interactively
ce generate-tasks --interactive

# Generate directly from a User Story conversation
ce generate-tasks --from-us --output ./tasks_from_us
```

---

### Validation Commands

#### `ce validate` - Validate Artifacts / Validar Artefatos

Runs Deep Cross-Validation over PRPs, PRD, Tasks and contracts (`cli/commands/generation.py`). / Executa validação profunda entre PRPs, PRD, Tasks e contratos.

**Syntax / Sintaxe:**
```bash
ce validate PRPS_DIR [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `PRPS_DIR` | Required directory containing the phases to validate. / Pasta com os PRPs. | — |
| `--prd-file PATH` | Structured PRD for consistency checks. | optional |
| `--tasks-dir PATH` | TASKs folder to ensure inverse traceability. | optional |
| `--api-spec PATH` | OpenAPI/contract file for Deep Cross-Validation. | optional |
| `--ui-tasks-dir PATH` | UI tasks for contract comparison. | optional |
| `--soft-check` | Advisory mode (no abort on failure). | `false` |
| `--dry-run` | Prints what would be validated. | `false` |
| `--help-contextual` | Shows contextual tips and exits. | `false` |
| `--commits-json PATH` | JSON mapping Tasks → commits/PRs. | optional |
| `--project-name TEXT` | Name used when recording metrics. | auto |
| `--ai/--no-ai` | Hybrid intelligence toggle. | project default |
| `--embedding-model TEXT` | Embedding alias or ID. | per config |

**Examples / Exemplos:**
```bash
# Validate full pipeline with contracts
ce validate ./prps --prd-file prd/prd_structured.json \
  --tasks-dir ./tasks --api-spec openapi.yaml --ui-tasks-dir ./ui_tasks

# Soft-check for Git hooks
ce validate ./prps --soft-check

# Dry-run only
ce validate ./prps --dry-run
```

---

### AI Governance Commands

#### `ce ai-governance status` - AI Governance Status / Status de Governança de IA

Shows current AI governance status including transformers availability, embedding model configuration and policy compliance (`cli/commands/ai_governance.py`, `core/ai_governance_service.py`). / Exibe status atual de governança de IA incluindo disponibilidade de transformers, configuração de modelo de embedding e conformidade de políticas.

**Syntax / Sintaxe:**
```bash
ce ai-governance status [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory to analyze. / Diretório do projeto. | `.` |
| `--format TEXT` | Output format (`text` or `json`). / Formato de saída. | `text` |

**Examples / Exemplos:**
```bash
# Text status with recommendations
ce ai-governance status

# JSON status for automation
ce ai-governance status --format json

# Status for specific project
ce ai-governance status --project-dir ./my-project
```

**Displayed Information:**
- Transformers availability status
- Current embedding model
- AI profile (local, balanced, corporate)
- Policy compliance status
- Recommendations for optimization

**Code References / Referências de Código:**
- Implementation: `cli/commands/ai_governance.py`
- Service: `core/ai_governance_service.py` (`resolve_preferences`, `dependencies_ready`)

---

#### `ce ai-governance install` - Install AI Dependencies / Instalar Dependências de IA

Installs dependencies needed for semantic AI mode including sentence-transformers and specified embedding models (`cli/commands/ai_governance.py`). / Instala dependências necessárias para modo IA semântico incluindo sentence-transformers e modelos de embedding especificados.

**Syntax / Sintaxe:**
```bash
ce ai-governance install [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--model TEXT` | Embedding model to install. / Modelo de embedding a instalar. | `all-minilm-l6-v2` |
| `--force` | Force reinstallation even if already installed. / Forçar reinstalação. | `false` |

**Examples / Exemplos:**
```bash
# Default installation (all-minilm-l6-v2)
ce ai-governance install

# Install specific model
ce ai-governance install --model all-mpnet-base-v2

# Force reinstallation
ce ai-governance install --model all-minilm-l6-v2 --force
```

**Installed Components:**
- `sentence-transformers` library
- Specified embedding model (~80-500MB depending on model)
- Required dependencies (torch, transformers, etc.)

**Code References / Referências de Código:**
- Implementation: `cli/commands/ai_governance.py`
- Service: `core/ai_governance_service.py`

---

#### `ce ai-governance set-model` - Configure Embedding Model / Configurar Modelo de Embedding

Sets the embedding model for the project and updates configuration (`cli/commands/ai_governance.py`, `core/config_service.py`). / Define o modelo de embedding para o projeto e atualiza a configuração.

**Syntax / Sintaxe:**
```bash
ce ai-governance set-model MODEL [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `MODEL` | Embedding model name. / Nome do modelo de embedding. | required |
| `--project-dir PATH` | Project directory to configure. / Diretório do projeto. | `.` |

**Available Models / Modelos Disponíveis:**
- `all-minilm-l6-v2` - Default, fast, 384 dimensions (~80MB)
- `all-mpnet-base-v2` - Better quality, 768 dimensions (~420MB)
- `bge-small-en-v1.5` - Optimized for English, 384 dimensions (~130MB)
- `bge-base-en-v1.5` - Higher quality, 768 dimensions (~420MB)

**Examples / Exemplos:**
```bash
# Set default fast model
ce ai-governance set-model all-minilm-l6-v2

# Set high-quality model
ce ai-governance set-model all-mpnet-base-v2

# Set for specific project
ce ai-governance set-model bge-small-en-v1.5 --project-dir ./my-project
```

**Configuration Updated:**
- `.ce-config.json` - `embedding_model` field updated
- Model will be downloaded on first use if not already cached

**Code References / Referências de Código:**
- Implementation: `cli/commands/ai_governance.py`
- Services: `core/ai_governance_service.py`, `core/config_service.py`

---

### DevOps Commands

#### `ce autopilot` - Autopilot Mode / Modo Autopilot

Executes the entire Context Engineer pipeline flexibly, adapting to available inputs (`cli/commands/autopilot.py`, `core/autopilot_service.py`). / Executa o pipeline completo do Context Engineer de forma flexível, adaptando-se às entradas disponíveis.

**Syntax / Sintaxe:**
```bash
ce autopilot [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory (created if missing). / Diretório do projeto. | `.` |
| `--project-name TEXT` | Project name (defaults to folder name). / Nome do projeto. | auto |
| `--stack TEXT` | Stack to apply during init when needed. / Stack a aplicar. | `python-fastapi` |
| `--idea-file PATH` | Idea/PRD seed file (optional). When provided, PRD generation runs automatically. / Arquivo com ideia. | optional |
| `--prd-file PATH` | Existing structured PRD (optional). Use when `prd_structured.json` already exists. / PRD estruturado existente. | optional |
| `--prps-dir PATH` | Directory containing ready PRPs (optional). / Diretório com PRPs prontos. | optional |
| `--tasks-dir PATH` | Directory with pre-generated Tasks (optional). / Diretório com Tasks pré-geradas. | optional |
| `--skip-validate` | Skip final validation stage. / Pula validação final. | `false` |
| `--tasks-from-us` | Create tasks from an interactive User Story. / Cria tasks via User Story interativa. | `false` |
| `--ai/--no-ai` | Hybrid intelligence toggle. / Modo de inteligência. | project default |
| `--embedding-model TEXT` | Embedding model alias or full name. / Modelo de embedding. | per config |

**Examples / Exemplos:**
```bash
# Complete autopilot from idea file
ce autopilot --idea-file docs/product-idea.md --project-dir ./my-project

# Resume from existing PRD
ce autopilot --prd-file prd/prd_structured.json --project-dir ./my-project

# Skip validation for quick iteration
ce autopilot --idea-file idea.txt --skip-validate

# Generate tasks from User Story interactively
ce autopilot --tasks-from-us --project-dir ./feature-branch
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/autopilot.py`
- Service: `core/autopilot_service.py` (lines 17-194)

---

### Status & Reporting Commands

#### `ce status` - Project Status / Status do Projeto

Shows current Context Engineer project status with progress and metrics (`cli/commands/status.py`, `core/project_status_service.py`). / Exibe o status atual do projeto Context Engineer com progresso e métricas.

**Syntax / Sintaxe:**
```bash
ce status [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory to analyze. / Diretório do projeto. | `.` |
| `--json` | Output in JSON format. / Saída em formato JSON. | `false` |
| `--ai/--no-ai` | Hybrid intelligence toggle for suggestions. / Modo de inteligência para sugestões. | project default |
| `--embedding-model TEXT` | Embedding model for semantic search. / Modelo de embedding. | per config |

**Examples / Exemplos:**
```bash
# Basic status with suggestions
ce status

# JSON output for automation
ce status --json --project-dir ./my-project

# Status with AI-powered suggestions
ce status --ai --embedding-model all-minilm-l6-v2
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/status.py` (lines 16-49)
- Service: `core/project_status_service.py` (`gather_status_data`, `format_status_text`)

---

#### `ce doctor` - Project Diagnostics / Diagnóstico do Projeto

Runs complete project diagnostics including Git hooks, AI dependencies, configuration and suggests fixes (`cli/commands/doctor.py`). / Executa diagnóstico completo incluindo hooks Git, dependências de IA, configuração e sugere correções.

**Syntax / Sintaxe:**
```bash
ce doctor [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory to diagnose. / Diretório do projeto. | `.` |
| `--format TEXT` | Output format (`text`, `table`, `json`). / Formato de saída. | `text` |
| `--ai-profile TEXT` | AI profile to check/apply (`local`, `balanced`, `corporate`). / Perfil de IA. | `None` |
| `--apply-profile` | Apply the specified AI profile to project. / Aplicar perfil ao projeto. | `false` |

**Examples / Exemplos:**
```bash
# Basic diagnostics
ce doctor

# Table format for better readability
ce doctor --format table

# Check and apply corporate AI profile
ce doctor --ai-profile corporate --apply-profile

# JSON output for CI/CD integration
ce doctor --format json --project-dir ./my-project
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/doctor.py`
- Services: `core/ai_governance_service.py`, `core/config_service.py`, `core/git_service.py`

---

#### `ce checklist` - Project Checklist / Checklist do Projeto

Displays an interactive project checklist showing completion status of all phases (`cli/commands/status.py`). / Exibe checklist interativo mostrando status de conclusão de todas as fases.

**Syntax / Sintaxe:**
```bash
ce checklist [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory to analyze. / Diretório do projeto. | `.` |

**Examples / Exemplos:**
```bash
# Display checklist for current project
ce checklist

# Display checklist for specific project
ce checklist --project-dir ./my-project
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/status.py` (lines 52-66)
- Service: `core/project_status_service.py` (`format_checklist_text`)

---

#### `ce assist` - Conversational Assistant / Assistente Conversacional

Conversational assistant mode with guided steps, pattern suggestions and optional HTML report (`cli/commands/status.py`, `core/project_status_service.py`). / Modo assistente conversacional com passos guiados, sugestões de padrões e relatório HTML opcional.

**Syntax / Sintaxe:**
```bash
ce assist [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory to analyze. / Diretório do projeto. | `.` |
| `--format TEXT` | Output format (`text` or `html`). / Formato de saída. | `text` |
| `--output-file PATH` | Report destination when format is html. / Destino do relatório HTML. | `assist_report.html` |
| `--open` | Open HTML report in browser automatically. / Abrir relatório no navegador. | `false` |
| `--ai/--no-ai` | Hybrid intelligence toggle for suggestions. / Modo de inteligência. | project default |
| `--embedding-model TEXT` | Embedding model for semantic search. / Modelo de embedding. | per config |

**Examples / Exemplos:**
```bash
# Text-based assistant
ce assist

# Generate HTML report and open in browser
ce assist --format html --open

# Generate HTML report to specific file
ce assist --format html --output-file docs/assistant-report.html

# Assistant with AI-powered suggestions
ce assist --ai --embedding-model all-minilm-l6-v2
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/status.py` (lines 69-221)
- Service: `core/project_status_service.py` (`run_assistant_flow`, `render_assist_intro`)

---

#### `ce wizard` - Interactive Wizard / Assistente Interativo

Interactive wizard that guides through the entire Context Engineer workflow with confirmations at each step (`cli/commands/status.py`). / Assistente interativo que guia por todo o fluxo do Context Engineer com confirmações em cada etapa.

**Syntax / Sintaxe:**
```bash
ce wizard [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory to work with. / Diretório do projeto. | `.` |
| `--ai/--no-ai` | Hybrid intelligence toggle. / Modo de inteligência. | project default |
| `--embedding-model TEXT` | Embedding model for AI mode. / Modelo de embedding. | per config |

**Examples / Exemplos:**
```bash
# Start interactive wizard
ce wizard

# Wizard with AI-powered suggestions
ce wizard --ai --embedding-model all-minilm-l6-v2

# Wizard for specific project
ce wizard --project-dir ./my-project
```

**Workflow Steps:**
1. Check if project is initialized (run `ce init` if needed)
2. Check if PRD exists (run `ce generate-prd` if needed)
3. Check if PRPs exist (run `ce generate-prps` if needed)
4. Check if Tasks exist (run `ce generate-tasks` if needed)
5. Display completion summary and next steps

**Code References / Referências de Código:**
- Implementation: `cli/commands/status.py` (lines 223-350)
- Service: `core/project_status_service.py`
- Related: Uses `ce init`, `ce generate-prd`, `ce generate-prps`, `ce generate-tasks`

---

#### `ce report` - Project Report / Relatório do Projeto

Generates comprehensive project report with metrics, ROI tracking and governance status (`cli/commands/reporting.py`, `core/reporting_service.py`). / Gera relatório abrangente do projeto com métricas, tracking de ROI e status de governança.

**Syntax / Sintaxe:**
```bash
ce report [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-name TEXT` | Project name for metrics lookup. / Nome do projeto. | auto-detect |
| `--output PATH` | Output file path. / Caminho do arquivo de saída. | `stdout` |
| `--format TEXT` | Output format (`text`, `html`, `json`). / Formato de saída. | `text` |

**Examples / Exemplos:**
```bash
# Text report to console
ce report --project-name my-api

# HTML report to file
ce report --project-name my-api --format html --output report.html

# JSON report for automation
ce report --project-name my-api --format json --output report.json
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/reporting.py`
- Service: `core/reporting_service.py`, `core/metrics.py`
- Templates: `templates/reporting/*.j2`

---

#### `ce metrics-summary` - Metrics Summary / Resumo de Métricas

Displays quick summary of project metrics including story points and rework rate (`cli/commands/reporting.py`, `core/metrics.py`). / Exibe resumo rápido das métricas do projeto incluindo story points e taxa de retrabalho.

**Syntax / Sintaxe:**
```bash
ce metrics-summary [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-name TEXT` | Project name for metrics. / Nome do projeto. | auto-detect |
| `--tasks-dir PATH` | Tasks directory for story points calculation. / Diretório de tasks. | `./tasks` |

**Examples / Exemplos:**
```bash
# Quick metrics summary
ce metrics-summary --project-name my-api

# Summary with specific tasks directory
ce metrics-summary --project-name my-api --tasks-dir ./TASKs
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/reporting.py`
- Service: `core/metrics.py` (`get_project_metrics`)

---

#### `ce ai-status` - AI Status / Status da IA

Displays current AI configuration and dependencies status (`cli/commands/reporting.py`, `core/ai_governance_service.py`). / Exibe configuração atual de IA e status das dependências.

**Syntax / Sintaxe:**
```bash
ce ai-status [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory. / Diretório do projeto. | `.` |
| `--format TEXT` | Output format (`text` or `json`). / Formato de saída. | `text` |

**Examples / Exemplos:**
```bash
# Display AI status
ce ai-status

# JSON output for automation
ce ai-status --format json
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/reporting.py`
- Service: `core/ai_governance_service.py`

---

### Marketplace Commands

#### `ce marketplace list` - List Marketplace Items / Listar Itens do Marketplace

Lists available marketplace items with optional filters by category and stack (`cli/commands/marketplace.py`, `core/marketplace_service.py`). / Lista itens disponíveis do marketplace com filtros opcionais por categoria e stack.

**Syntax / Sintaxe:**
```bash
ce marketplace list [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--category TEXT` | Filter by category (authentication, api-patterns, security, etc). / Filtrar por categoria. | all |
| `--stack TEXT` | Filter by stack (python-fastapi, node-react, etc). / Filtrar por stack. | all |

**Examples / Exemplos:**
```bash
# List all marketplace items
ce marketplace list

# List security patterns
ce marketplace list --category security

# List Python FastAPI items
ce marketplace list --stack python-fastapi

# List security patterns for Python
ce marketplace list --category security --stack python-fastapi
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/marketplace.py` (lines 17-30)
- Service: `core/marketplace_service.py` (`load_catalog`)

---

#### `ce marketplace install` - Install Marketplace Item / Instalar Item do Marketplace

Installs a marketplace item (pattern, template, workflow) into the project (`cli/commands/marketplace.py`, `core/marketplace_service.py`). / Instala um item do marketplace (padrão, template, workflow) no projeto.

**Syntax / Sintaxe:**
```bash
ce marketplace install ITEM_ID [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `ITEM_ID` | Unique identifier of the marketplace item. / Identificador único do item. | required |
| `--project-dir PATH` | Target project directory. / Diretório do projeto destino. | `.` |

**Examples / Exemplos:**
```bash
# Install JWT authentication pattern
ce marketplace install pattern_auth_jwt_fastapi

# Install to specific project
ce marketplace install pattern_api_gateway --project-dir ./my-project

# Install CI/CD workflow
ce marketplace install hook_ci_traceability --project-dir .
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/marketplace.py` (lines 33-69)
- Service: `core/marketplace_service.py` (`find_item`, `copy_resource`)

---

### Pattern Library Commands

#### `ce patterns list` - List Patterns / Listar Padrões

Lists available code patterns from the library with optional filters (`cli/commands/patterns.py`). / Lista padrões de código disponíveis da biblioteca com filtros opcionais.

**Syntax / Sintaxe:**
```bash
ce patterns list [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--stack TEXT` | Filter by stack (python-fastapi, node-react, etc). / Filtrar por stack. | all |
| `--category TEXT` | Filter by category (authentication, api, security, etc). / Filtrar por categoria. | all |

**Examples / Exemplos:**
```bash
# List all patterns
ce patterns list

# List Python FastAPI patterns
ce patterns list --stack python-fastapi

# List authentication patterns
ce patterns list --category authentication
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/patterns.py` (lines 32-70)
- Service: `core/engine.py` (`pattern_library`)

---

#### `ce patterns show` - Show Pattern Details / Exibir Detalhes do Padrão

Displays detailed information about a specific pattern including code examples (`cli/commands/patterns.py`). / Exibe informações detalhadas sobre um padrão específico incluindo exemplos de código.

**Syntax / Sintaxe:**
```bash
ce patterns show PATTERN_ID [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `PATTERN_ID` | Unique identifier of the pattern. / Identificador único do padrão. | required |

**Examples / Exemplos:**
```bash
# Show JWT authentication pattern
ce patterns show AUTH.JWT

# Show RESTful CRUD pattern
ce patterns show API.REST.CRUD
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/patterns.py` (lines 73-95)
- Service: `core/engine.py` (`pattern_library`)

---

#### `ce patterns suggest` - Suggest Patterns / Sugerir Padrões

Suggests relevant patterns based on project context and requirements using semantic search (`cli/commands/patterns.py`, `core/cache.py`). / Sugere padrões relevantes baseado no contexto e requisitos do projeto usando busca semântica.

**Syntax / Sintaxe:**
```bash
ce patterns suggest [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory to analyze. / Diretório do projeto. | `.` |
| `--ai/--no-ai` | Use semantic search for suggestions. / Usar busca semântica. | project default |
| `--embedding-model TEXT` | Embedding model for semantic search. / Modelo de embedding. | per config |

**Examples / Exemplos:**
```bash
# Suggest patterns for current project
ce patterns suggest

# Suggest with AI-powered semantic search
ce patterns suggest --ai --embedding-model all-minilm-l6-v2

# Suggest for specific project
ce patterns suggest --project-dir ./my-api
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/patterns.py` (lines 98-151)
- Services: `core/engine.py` (`pattern_library`), `core/cache.py` (`search_similar`)

---

### Provider Commands

#### `ce provider list` - List Providers / Listar Provedores

Lists all supported LLM providers with their default models and configuration status (`cli/commands/provider.py`). / Lista todos os provedores LLM suportados com seus modelos padrão e status de configuração.

**Syntax / Sintaxe:**
```bash
ce provider list
```

**Examples / Exemplos:**
```bash
ce provider list
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/provider.py`
- Service: `core/llm_provider.py` (`LLMProviderService.list_providers`)

---

#### `ce provider setup` - Configure Provider / Configurar Provedor

Interactively configure an LLM provider for the project, including API key storage and model selection (`cli/commands/provider.py`, `core/llm_provider.py`). / Configura interativamente um provedor LLM para o projeto, incluindo armazenamento de API key e seleção de modelo.

**Syntax / Sintaxe:**
```bash
ce provider setup [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--provider-id TEXT` | Provider to configure (skip interactive selection). / Provedor a configurar. | interactive |
| `--model TEXT` | Override the default model. The name must match the provider's API. / Modelo customizado. O nome deve ser idêntico ao da API do provedor. | provider default |
| `--port INT` | Custom port for local providers (Ollama / LM Studio). / Porta customizada para provedores locais. | provider default |
| `--project-dir PATH` | Project directory to save configuration. / Diretório do projeto. | `.` |

**Examples / Exemplos:**
```bash
# Interactive setup
ce provider setup

# Direct setup with custom model
ce provider setup --provider-id openai --model gpt-4-turbo

# Local Ollama with custom port
ce provider setup --provider-id local-ollama --model codellama:13b --port 11434
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/provider.py`
- Services: `core/llm_provider.py`, `core/config_service.py`

---

#### `ce provider set-model` - Set Custom Model / Definir Modelo Customizado

Set or change the LLM model for a provider in the project configuration. The model name **must match exactly** what the provider's API expects (`cli/commands/provider.py`). / Define ou altera o modelo LLM de um provedor na configuração do projeto. O nome do modelo **deve ser idêntico** ao que a API do provedor espera.

**Syntax / Sintaxe:**
```bash
ce provider set-model PROVIDER_ID MODEL_NAME [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `PROVIDER_ID` | Provider identifier (openai, gemini, anthropic, etc). / Identificador do provedor. | required |
| `MODEL_NAME` | Model name as expected by the provider's API. / Nome do modelo conforme a API do provedor. | required |
| `--project-dir PATH` | Project directory. / Diretório do projeto. | `.` |

**Examples / Exemplos:**
```bash
# Set custom OpenAI model
ce provider set-model openai gpt-4-turbo

# Set Gemini model
ce provider set-model gemini gemini-1.5-pro

# Set Anthropic model
ce provider set-model anthropic claude-opus-4-20250514

# Set local Ollama model
ce provider set-model local-ollama codellama:13b
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/provider.py`
- Service: `core/config_service.py`

---

#### `ce provider set-key` - Store API Key / Armazenar API Key

Prompt for and securely store an encrypted API key for a provider (`cli/commands/provider.py`, `core/llm_provider.py`). / Solicita e armazena de forma criptografada uma API key para um provedor.

**Syntax / Sintaxe:**
```bash
ce provider set-key PROVIDER_ID
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `PROVIDER_ID` | Provider identifier (only API providers). / Identificador do provedor (apenas provedores API). | required |

**Examples / Exemplos:**
```bash
ce provider set-key openai
ce provider set-key gemini
ce provider set-key anthropic
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/provider.py`
- Service: `core/llm_provider.py` (`_CredentialVault`)

---

#### `ce provider remove-key` - Remove API Key / Remover API Key

Remove a stored API key for a provider (`cli/commands/provider.py`). / Remove uma API key armazenada de um provedor.

**Syntax / Sintaxe:**
```bash
ce provider remove-key PROVIDER_ID
```

**Examples / Exemplos:**
```bash
ce provider remove-key openai
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/provider.py`
- Service: `core/llm_provider.py`

---

#### `ce provider show` - Show Configuration / Exibir Configuração

Display the resolved LLM provider configuration for the project, including model (with custom indicator), API key status, and custom port (`cli/commands/provider.py`). / Exibe a configuração resolvida do provedor LLM do projeto, incluindo modelo (com indicador de customizado), status da API key e porta customizada.

**Syntax / Sintaxe:**
```bash
ce provider show [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory. / Diretório do projeto. | `.` |

**Examples / Exemplos:**
```bash
ce provider show
ce provider show --project-dir ./my-project
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/provider.py`
- Services: `core/llm_provider.py`, `core/config_service.py`

---

### DevOps Commands

#### `ce install-hooks` - Install Git Hooks / Instalar Hooks Git

Installs Git hooks for automatic validation (pre-commit, pre-push) with Soft-Gate or Hard-Gate mode (`cli/commands/devops.py`, `core/git_service.py`). / Instala hooks Git para validação automática (pre-commit, pre-push) com modo Soft-Gate ou Hard-Gate.

**Syntax / Sintaxe:**
```bash
ce install-hooks [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory with Git repository. / Diretório do projeto com repositório Git. | `.` |
| `--hard-gate` | Enable Hard-Gate mode (blocks push on validation failure). / Habilitar modo Hard-Gate. | `false` |

**Examples / Exemplos:**
```bash
# Install Soft-Gate hooks (advisory mode)
ce install-hooks

# Install Hard-Gate hooks (blocking mode)
ce install-hooks --hard-gate

# Install hooks for specific project
ce install-hooks --project-dir ./my-project
```

**Hooks Installed:**
- `pre-commit`: Quick validation of JSON/YAML syntax
- `pre-push`: Full validation with `ce validate --soft-check`

**Code References / Referências de Código:**
- Implementation: `cli/commands/devops.py`
- Service: `core/git_service.py` (`GitHookManager`)

---

#### `ce ci-bootstrap` - Bootstrap CI/CD / Configurar CI/CD

Generates CI/CD workflow files (GitHub Actions, GitLab CI) with Context Engineer validation (`cli/commands/devops.py`, `core/git_service.py`). / Gera arquivos de workflow CI/CD (GitHub Actions, GitLab CI) com validação do Context Engineer.

**Syntax / Sintaxe:**
```bash
ce ci-bootstrap [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory. / Diretório do projeto. | `.` |
| `--platform TEXT` | CI/CD platform (`github`, `gitlab`). / Plataforma de CI/CD. | `github` |

**Examples / Exemplos:**
```bash
# Generate GitHub Actions workflow
ce ci-bootstrap

# Generate GitLab CI configuration
ce ci-bootstrap --platform gitlab

# Generate for specific project
ce ci-bootstrap --project-dir ./my-project --platform github
```

**Generated Files:**
- GitHub: `.github/workflows/context-engineer.yml`
- GitLab: `.gitlab-ci.yml`

**Code References / Referências de Código:**
- Implementation: `cli/commands/devops.py`
- Service: `core/git_service.py`

---

#### `ce ide sync` - Sync IDE Rules / Sincronizar Regras da IDE

Synchronizes IDE rules, prompts and workflows from the Context Engineer repository to the project (`cli/commands/ide.py`). / Sincroniza regras da IDE, prompts e workflows do repositório Context Engineer para o projeto.

**Syntax / Sintaxe:**
```bash
ce ide sync [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Target project directory. / Diretório do projeto destino. | `.` |

**Examples / Exemplos:**
```bash
# Sync IDE rules to current project
ce ide sync

# Sync to specific project
ce ide sync --project-dir ./my-project
```

**Synced Content:**
- Prompts: `Agente_PRD_360.md`, `Agente_PRP_Orquestrador.md`, etc.
- Workflows: Phase templates (F0-F9)
- Rules: `GLOBAL_ENGINEERING_RULES.json`, `PROJECT_STANDARDS.md`

**Code References / Referências de Código:**
- Implementation: `cli/commands/ide.py`

---

### Intelligence Modes

Context Engineer supports two intelligence modes:

#### Light Mode (Levenshtein)

**Characteristics:**
- No external dependencies
- Fast and lightweight
- Works offline
- String similarity search
- Less semantically accurate

**Usage:**
```bash
ce <command> --enable-ai false
```

#### Semantic Mode (Transformers)

**Characteristics:**
- Advanced semantic search
- Understands context and meaning
- More accurate recommendations
- Requires `sentence-transformers`
- First use downloads model (~80MB)

**Usage:**
```bash
ce <command> --enable-ai true --embedding-model all-minilm-l6-v2
```

---

### Utility Commands

#### `ce check-dependencies` - Check Task Dependencies / Verificar Dependências de Tasks

Analyzes and validates dependencies between tasks to ensure correct execution order (`cli/commands/generation.py`). / Analisa e valida dependências entre tasks para garantir ordem correta de execução.

**Syntax / Sintaxe:**
```bash
ce check-dependencies TASKS_DIR [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `TASKS_DIR` | Directory containing task files. / Diretório com arquivos de tasks. | required |
| `--ai/--no-ai` | Use AI for dependency analysis. / Usar IA para análise. | project default |
| `--embedding-model TEXT` | Embedding model for semantic analysis. / Modelo de embedding. | per config |

**Examples / Exemplos:**
```bash
# Check dependencies in tasks directory
ce check-dependencies ./tasks

# Check with AI-powered analysis
ce check-dependencies ./tasks --ai --embedding-model all-minilm-l6-v2
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/generation.py` (lines 612-631)
- Service: `core/engine.py`

---

#### `ce estimate-effort` - Estimate Task Effort / Estimar Esforço da Task

Estimates effort (story points) for a single task based on complexity, stack and historical data (`cli/commands/generation.py`, `core/planning.py`). / Estima esforço (story points) para uma task baseado em complexidade, stack e dados históricos.

**Syntax / Sintaxe:**
```bash
ce estimate-effort TASK_FILE [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `TASK_FILE` | Path to task JSON file. / Caminho para arquivo JSON da task. | required |
| `--stack TEXT` | Technology stack for estimation. / Stack tecnológica. | `python-fastapi` |
| `--project-name TEXT` | Project name for historical adjustments. / Nome do projeto. | optional |
| `--ai/--no-ai` | Use AI for estimation. / Usar IA para estimativa. | project default |
| `--embedding-model TEXT` | Embedding model. / Modelo de embedding. | per config |

**Examples / Exemplos:**
```bash
# Estimate single task
ce estimate-effort tasks/TASK.FR-001.json

# Estimate with specific stack
ce estimate-effort tasks/TASK.FR-001.json --stack node-react

# Estimate with historical data
ce estimate-effort tasks/TASK.FR-001.json --project-name my-api --stack python-fastapi
```

**Output:**
- Story points estimate
- Complexity breakdown
- Confidence level
- Historical comparison (if project-name provided)

**Code References / Referências de Código:**
- Implementation: `cli/commands/generation.py` (lines 634-677)
- Service: `core/planning.py` (`EffortEstimator`)

---

#### `ce estimate-batch` - Batch Effort Estimation / Estimativa em Lote

Estimates effort (story points) for multiple tasks at once with aggregated statistics (`cli/commands/generation.py`, `core/planning.py`). / Estima esforço (story points) para múltiplas tasks de uma vez com estatísticas agregadas.

**Syntax / Sintaxe:**
```bash
ce estimate-batch TASKS_DIR [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `TASKS_DIR` | Directory containing task files. / Diretório com arquivos de tasks. | required |
| `--stack TEXT` | Technology stack for estimation. / Stack tecnológica. | `python-fastapi` |
| `--project-name TEXT` | Project name for historical adjustments. / Nome do projeto. | optional |
| `--output PATH` | Export results to JSON file. / Exportar resultados para JSON. | optional |
| `--ai/--no-ai` | Use AI for estimation. / Usar IA para estimativa. | project default |
| `--embedding-model TEXT` | Embedding model. / Modelo de embedding. | per config |

**Examples / Exemplos:**
```bash
# Estimate all tasks in directory
ce estimate-batch ./tasks

# Estimate with specific stack and export
ce estimate-batch ./tasks --stack node-react --output estimates.json

# Estimate with historical data
ce estimate-batch ./tasks --project-name my-api --stack python-fastapi
```

**Output:**
- Individual task estimates
- Total story points
- Average complexity
- Distribution by complexity level
- Confidence metrics

**Code References / Referências de Código:**
- Implementation: `cli/commands/generation.py` (lines 680-764)
- Service: `core/planning.py` (`EffortEstimator`)

---

#### `ce generate-commit-map` - Generate Commit Mapping / Gerar Mapeamento de Commits

Generates commits.json file mapping tasks to Git commits and pull requests for traceability (`cli/commands/commit.py`). / Gera arquivo commits.json mapeando tasks para commits Git e pull requests para rastreabilidade.

**Syntax / Sintaxe:**
```bash
ce generate-commit-map [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--project-dir PATH` | Project directory with Git repository. / Diretório do projeto. | `.` |
| `--output PATH` | Output file path. / Caminho do arquivo de saída. | `commits.json` |
| `--tasks-dir PATH` | Tasks directory. / Diretório de tasks. | `./tasks` |
| `--branch TEXT` | Git branch to analyze. / Branch Git a analisar. | current |

**Examples / Exemplos:**
```bash
# Generate commit mapping for current project
ce generate-commit-map

# Generate for specific branch
ce generate-commit-map --branch main --output main-commits.json

# Generate for specific project
ce generate-commit-map --project-dir ./my-project --tasks-dir ./my-project/tasks
```

**Generated File Structure:**
```json
{
  "TASK.FR-001": {
    "commits": ["abc123", "def456"],
    "pull_requests": ["#42"],
    "status": "completed"
  }
}
```

**Code References / Referências de Código:**
- Implementation: `cli/commands/commit.py`
- Service: `cli/shared.py` (`build_commit_mapping`)

---

### Quick Start and Discovery Commands

#### `ce quickstart` - Quick Start Guide / Guia de Início Rápido

5-minute quick guide to get started with Context Engineer with optional interactive tutorial (`cli/commands/quickstart.py`). / Guia rápido de 5 minutos para começar com Context Engineer com tutorial interativo opcional.

**Syntax / Sintaxe:**
```bash
ce quickstart [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--skip-intro` | Skip introduction and go straight to setup. / Pular introdução. | `false` |
| `--interactive / -i` | Full tutorial mode with detailed explanations (15 min). / Modo tutorial completo. | `false` |
| `--example TEXT` | Use pre-configured example (`todo-app`, `blog`, `ecommerce`, `api`). / Usar exemplo pré-configurado. | optional |

**Examples / Exemplos:**
```bash
# Quick 5-minute guide
ce quickstart

# Skip intro and start setup
ce quickstart --skip-intro

# Full interactive tutorial
ce quickstart --interactive

# Start with example project
ce quickstart --example todo-app
```

**Tutorial Covers:**
- Installation verification
- First project initialization
- PRD generation basics
- PRPs and tasks overview
- Validation workflow
- Next steps and resources

**Code References / Referências de Código:**
- Implementation: `cli/commands/quickstart.py`

---

#### `ce explore` - Explore Commands / Explorar Comandos

Explores available commands organized by category to help users discover features (`cli/commands/explore.py`). / Explora comandos disponíveis organizados por categoria para ajudar usuários a descobrir funcionalidades.

**Syntax / Sintaxe:**
```bash
ce explore [OPTIONS]
```

| Option / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `--category TEXT` | Filter by specific category. / Filtrar por categoria específica. | all |

**Examples / Exemplos:**
```bash
# Show all commands by category
ce explore

# Show only generation commands
ce explore --category generation

# Show only DevOps commands
ce explore --category devops
```

**Categories:**
- `generation` - PRD, PRPs, Tasks generation
- `validation` - Validation and quality checks
- `status` - Status, assist, wizard
- `governance` - AI governance and policies
- `marketplace` - Marketplace and patterns
- `devops` - CI/CD, hooks, deployment
- `reporting` - Metrics, reports, dashboards
- `utilities` - Dependencies, estimation, commit mapping

**Code References / Referências de Código:**
- Implementation: `cli/commands/explore.py`

---

#### `ce mock-server` - Launch Mock Server / Iniciar Servidor Mock

Launches an ephemeral mock server from an OpenAPI specification for testing (`cli/commands/devops.py`). / Inicia servidor mock efêmero a partir de especificação OpenAPI para testes.

**Syntax / Sintaxe:**
```bash
ce mock-server OPENAPI_SPEC [OPTIONS]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `OPENAPI_SPEC` | Path to OpenAPI specification file. / Caminho para arquivo OpenAPI. | required |
| `--port INTEGER` | Mock server port. / Porta do servidor mock. | `4010` |

**Examples / Exemplos:**
```bash
# Launch mock server on default port
ce mock-server openapi.yaml

# Launch on custom port
ce mock-server openapi.yaml --port 8080

# Launch with JSON spec
ce mock-server api-spec.json --port 3000
```

**Features:**
- Automatic response generation from OpenAPI spec
- Request validation
- Response examples from spec
- Hot reload on spec changes

**Code References / Referências de Código:**
- Implementation: `cli/commands/devops.py` (lines 100-103)

---

#### `ce alias` - Manage Command Aliases / Gerenciar Aliases de Comandos

Manages handy aliases for common commands to speed up workflow (`cli/commands/alias.py`). / Gerencia aliases úteis para comandos comuns para acelerar o workflow.

**Syntax / Sintaxe:**
```bash
ce alias ACTION [ALIAS] [COMMAND]
```

| Argument / Opção | Description / Descrição | Default |
| --- | --- | --- |
| `ACTION` | Action to perform (`list`, `add`, `remove`). / Ação a executar. | `list` |
| `ALIAS` | Alias name (for add/remove). / Nome do alias. | optional |
| `COMMAND` | Full command (for add). / Comando completo. | optional |

**Examples / Exemplos:**
```bash
# List all aliases
ce alias list

# Add new alias
ce alias add gpr "generate-prps"
ce alias add val "validate --soft-check"

# Remove alias
ce alias remove gpr

# Use alias
ce gpr prd/prd_structured.json
```

**Common Aliases:**
- `gpr` → `generate-prps`
- `gt` → `generate-tasks`
- `val` → `validate`
- `st` → `status`

**Code References / Referências de Código:**
- Implementation: `cli/commands/alias.py`

---

### Per-Project Configuration

Each Context Engineer project has its own configuration and SQLite database.

#### Configuration File: `.ce-config.json`

```json
{
  "project_name": "my-project",
  "stack": "python-fastapi",
  "use_transformers": true,
  "embedding_model": "all-minilm-l6-v2",
  "created_at": "2026-01-07T10:00:00",
  "version": "1.0.0"
}
```

#### Database: `.ce-intelligence.db`

Each project has its own SQLite with:

**Tables:**
- `patterns` - Reusable code patterns
- `embeddings` - Semantic vectors for search
- `metrics` - Project metrics
- `token_usage` - Token usage tracking
- `prompt_history` - Prompt and response history
- `validations` - Validation history

**Benefits:**
- Complete isolation between projects
- Project-specific metrics
- Per-project embedding cache
- Per-project token traceability
- Easy backup and migration

---

### Usage Examples

#### Complete Flow: New Project

```bash
# 1. Initialize project
ce init my-api --stack python-fastapi --enable-ai true

# 2. Enter directory
cd my-api

# 3. Generate PRD (interactive mode)
ce generate-prd --interactive

# 4. Generate PRPs
ce generate-prps prd/product.md

# 5. Validate everything
ce validate --check-traceability --check-contracts

# 6. Generate tasks
ce generate-tasks

# 7. View status
ce status --detailed

# 8. View metrics
ce metrics
```

---

## Versão em Português

### Índice

- [Visão Geral](#visao-geral)
- [Instalação](#instalacao)
- [Comandos de Geração](#comandos-de-geracao)
- [Comandos de Validação](#comandos-de-validacao)
- [Comandos de Governança de IA](#comandos-de-governanca-de-ia)
- [Comandos de DevOps](#comandos-de-devops)
- [Comandos de Marketplace](#comandos-de-marketplace)
- [Comandos de Status e Relatórios](#comandos-de-status-e-relatorios)
- [Comandos Utilitários](#comandos-utilitarios)
- [Modos de Inteligência](#modos-de-inteligencia)
- [Configuração por Projeto](#configuracao-por-projeto)
- [Exemplos de Uso](#exemplos-de-uso)

---

### Visão Geral

O Context Engineer é um framework CLI para engenharia de contexto e governança de IA em projetos de software. Ele fornece ferramentas para:

- Geração automatizada de PRD, PRPs e Tasks
- Validação de contratos e rastreabilidade
- Governança de IA e otimização de prompts
- Métricas e monitoramento de projetos
- Integração com Git e CI/CD

**Comando base:** `ce`

**Ajuda geral:**
```bash
ce --help
```

**Ajuda de comando específico:**
```bash
ce <comando> --help
```

---

### Instalação

#### Instalação via pip

```bash
pip install -e .
```

#### Instalação com dependências de IA

```bash
pip install -e ".[ai]"
```

#### Instalação para desenvolvimento

```bash
pip install -e ".[dev]"
```

#### Verificar instalação

```bash
ce --version
```

---

### Comandos de Geração

#### `ce init` - Inicializar Projeto

Cria a estrutura inicial de um projeto Context Engineer com templates, scaffolding e hooks Git.

**Sintaxe:**
```bash
ce init [PROJECT_NAME] [OPTIONS]
```

**Opções:**
- `--template TEXT` - Template a aplicar (padrão: `base`)
- `--stack TEXT` - Stack tecnológica (padrão: `python-fastapi`)
  - Opções: `python-fastapi`, `node-react`, `go-gin`, `vue3`
- `--output PATH` - Diretório de saída (padrão: `./`)
- `--git-hooks` - Gerar hooks Git para validação automática (padrão: `true`)
- `--enable-ai BOOL` - Modo de inteligência (IA ou leve)
- `--embedding-model TEXT` - Modelo de embedding para IA

**Exemplos:**
```bash
# Inicializar projeto Python FastAPI
ce init my-api --stack python-fastapi

# Inicializar com IA habilitada
ce init my-project --enable-ai true --embedding-model all-minilm-l6-v2

# Inicializar Node.js + React
ce init my-app --stack node-react --output ./projects/my-app
```

**Estrutura criada:**
```
my-project/
├── .ce-config.json          # Configuração do projeto
├── .ce-intelligence.db      # SQLite com cache e métricas
├── prd/                     # Product Requirements Documents
├── prp/                     # Product Requirement Phases
├── tasks/                   # Tasks geradas
├── .git/hooks/              # Git hooks para validação
└── [stack-specific files]   # Arquivos específicos do stack
```

---

#### `ce generate-prd` - Gerar PRD

Gera um Product Requirements Document a partir de uma ideia ou arquivo de entrada.

**Sintaxe:**
```bash
ce generate-prd [INPUT_FILE] [OPTIONS]
```

**Opções:**
- `--output PATH` - Diretório de saída (padrão: `./prd`)
- `--interactive, -i` - Modo conversacional interativo
- `--auto-validate` - Validar automaticamente após geração (padrão: `true`)
- `--preview` - Mostrar preview sem criar arquivos
- `--enable-ai BOOL` - Modo de inteligência
- `--embedding-model TEXT` - Modelo de embedding

**Exemplos:**
```bash
# Modo interativo
ce generate-prd --interactive

# A partir de arquivo
ce generate-prd idea.txt --output ./docs/prd

# Com preview
ce generate-prd idea.md --preview
```

---

#### `ce generate-prps` - Gerar PRPs

Gera Product Requirement Phases (fases de implementação) a partir de um PRD.

**Sintaxe:**
```bash
ce generate-prps [PRD_FILE] [OPTIONS]
```

**Opções:**
- `--output PATH` - Diretório de saída (padrão: `./prp`)
- `--auto-validate` - Validar automaticamente (padrão: `true`)
- `--enable-ai BOOL` - Modo de inteligência
- `--embedding-model TEXT` - Modelo de embedding

**Exemplos:**
```bash
# Gerar PRPs a partir de PRD
ce generate-prps prd/product.md

# Com validação automática
ce generate-prps prd/product.md --auto-validate
```

---

#### `ce generate-tasks` - Gerar Tasks

Gera tasks executáveis a partir de PRPs validados.

**Sintaxe:**
```bash
ce generate-tasks [OPTIONS]
```

**Opções:**
- `--prp-dir PATH` - Diretório com PRPs (padrão: `./prp`)
- `--output PATH` - Diretório de saída (padrão: `./tasks`)
- `--phase TEXT` - Fase específica para gerar tasks
- `--enable-ai BOOL` - Modo de inteligência
- `--embedding-model TEXT` - Modelo de embedding

**Exemplos:**
```bash
# Gerar todas as tasks
ce generate-tasks

# Gerar tasks de uma fase específica
ce generate-tasks --phase F1

# Com diretório customizado
ce generate-tasks --prp-dir ./docs/prp --output ./backlog
```

---

### Comandos de Validação

#### `ce validate` - Validar Artefatos

Valida PRD, PRPs e Tasks quanto a consistência, rastreabilidade e contratos.

**Sintaxe:**
```bash
ce validate [OPTIONS]
```

**Opções:**
- `--prd PATH` - Arquivo PRD para validar
- `--prp-dir PATH` - Diretório com PRPs
- `--tasks-dir PATH` - Diretório com tasks
- `--check-traceability` - Validar rastreabilidade completa
- `--check-contracts` - Validar contratos API vs UI
- `--strict` - Modo estrito (falha em warnings)

**Exemplos:**
```bash
# Validar tudo
ce validate --check-traceability --check-contracts

# Validar apenas PRPs
ce validate --prp-dir ./prp

# Validar rastreabilidade PRD → Tasks
ce validate --prd prd/product.md --tasks-dir ./tasks --check-traceability
```

---

### Comandos de Governança de IA

#### `ce ai-governance status` - Status de IA

Mostra o status atual da governança de IA no projeto.

**Sintaxe:**
```bash
ce ai-governance status [OPTIONS]
```

**Opções:**
- `--project-dir PATH` - Diretório do projeto (padrão: `.`)
- `--format TEXT` - Formato de saída (`text` ou `json`)

**Exemplos:**
```bash
# Status em texto
ce ai-governance status

# Status em JSON
ce ai-governance status --format json
```

---

#### `ce ai-governance install` - Instalar Dependências de IA

Instala dependências necessárias para o modo de IA semântica.

**Sintaxe:**
```bash
ce ai-governance install [OPTIONS]
```

**Opções:**
- `--model TEXT` - Modelo de embedding a instalar
- `--force` - Forçar reinstalação

**Exemplos:**
```bash
# Instalação padrão
ce ai-governance install

# Instalar modelo específico
ce ai-governance install --model all-minilm-l6-v2
```

---

#### `ce ai-governance set-model` - Configurar Modelo

Define o modelo de embedding para o projeto.

**Sintaxe:**
```bash
ce ai-governance set-model MODEL [OPTIONS]
```

**Modelos disponíveis:**
- `all-minilm-l6-v2` (padrão, rápido, 384 dim)
- `all-mpnet-base-v2` (melhor qualidade, 768 dim)
- `bge-small-en-v1.5` (otimizado, 384 dim)

**Exemplos:**
```bash
ce ai-governance set-model all-minilm-l6-v2
ce ai-governance set-model all-mpnet-base-v2 --project-dir ./my-project
```

---

### Comandos de DevOps

#### `ce autopilot` - Modo Autopilot

Executa o framework em modo autopilot, gerando PRD → PRPs → Tasks automaticamente.

**Sintaxe:**
```bash
ce autopilot [OPTIONS]
```

**Opções:**
- `--idea-file PATH` - Arquivo com a ideia do produto
- `--output PATH` - Diretório de saída
- `--validate-all` - Validar todos os artefatos
- `--enable-ai BOOL` - Modo de inteligência

**Exemplos:**
```bash
# Autopilot completo
ce autopilot --idea-file idea.txt --validate-all

# Com IA habilitada
ce autopilot --idea-file product-vision.md --enable-ai true
```

---

### Comandos de Status e Relatórios

#### `ce status` - Status do Projeto

Mostra o status atual do projeto Context Engineer.

**Sintaxe:**
```bash
ce status [OPTIONS]
```

**Opções:**
- `--project-dir PATH` - Diretório do projeto (padrão: `.`)
- `--detailed` - Mostrar informações detalhadas
- `--format TEXT` - Formato de saída (`text` ou `json`)

**Exemplos:**
```bash
# Status básico
ce status

# Status detalhado
ce status --detailed

# Status em JSON
ce status --format json --project-dir ./my-project
```

---

#### `ce doctor` - Diagnóstico do Projeto

Executa diagnóstico completo do projeto e sugere correções.

**Sintaxe:**
```bash
ce doctor [OPTIONS]
```

**Opções:**
- `--project-dir PATH` - Diretório do projeto
- `--fix` - Aplicar correções automaticamente
- `--format TEXT` - Formato de saída (`text` ou `json`)
- `--ai-profile TEXT` - Perfil de IA (`minimal`, `balanced`, `full`)
- `--apply-profile` - Aplicar perfil de IA

**Exemplos:**
```bash
# Diagnóstico básico
ce doctor

# Diagnóstico com correções automáticas
ce doctor --fix

# Aplicar perfil de IA balanceado
ce doctor --ai-profile balanced --apply-profile
```

---

#### `ce metrics` - Métricas do Projeto

Exibe métricas detalhadas do projeto.

**Sintaxe:**
```bash
ce metrics [OPTIONS]
```

**Opções:**
- `--project-dir PATH` - Diretório do projeto
- `--format TEXT` - Formato de saída (`text` ou `json`)
- `--export PATH` - Exportar métricas para arquivo

**Exemplos:**
```bash
# Métricas em texto
ce metrics

# Métricas em JSON
ce metrics --format json

# Exportar métricas
ce metrics --export metrics-report.json
```

---

### Modos de Inteligência

O Context Engineer suporta dois modos de inteligência:

#### Modo Light (Levenshtein)

**Características:**
- Sem dependências externas
- Rápido e leve
- Funciona offline
- Busca por similaridade de strings
- Menos preciso semanticamente

**Uso:**
```bash
ce <comando> --enable-ai false
```

#### Modo Semantic (Transformers)

**Características:**
- Busca semântica avançada
- Entende contexto e significado
- Recomendações mais precisas
- Requer `sentence-transformers`
- Primeiro uso baixa modelo (~80MB)

**Uso:**
```bash
ce <comando> --enable-ai true --embedding-model all-minilm-l6-v2
```

---

### Configuração por Projeto

Cada projeto Context Engineer possui sua própria configuração e banco de dados SQLite.

#### Arquivo de Configuração: `.ce-config.json`

```json
{
  "project_name": "my-project",
  "stack": "python-fastapi",
  "use_transformers": true,
  "embedding_model": "all-minilm-l6-v2",
  "created_at": "2026-01-07T10:00:00",
  "version": "1.0.0"
}
```

#### Banco de Dados: `.ce-intelligence.db`

Cada projeto possui seu próprio SQLite com:

**Tabelas:**
- `patterns` - Padrões de código reutilizáveis
- `embeddings` - Vetores semânticos para busca
- `metrics` - Métricas do projeto
- `token_usage` - Rastreamento de uso de tokens
- `prompt_history` - Histórico de prompts e respostas
- `validations` - Histórico de validações

**Benefícios:**
- Isolamento completo entre projetos
- Métricas específicas por projeto
- Cache de embeddings por projeto
- Rastreabilidade de tokens por projeto
- Fácil backup e migração

---

### Exemplos de Uso

#### Fluxo Completo: Novo Projeto

```bash
# 1. Inicializar projeto
ce init my-api --stack python-fastapi --enable-ai true

# 2. Entrar no diretório
cd my-api

# 3. Gerar PRD (modo interativo)
ce generate-prd --interactive

# 4. Gerar PRPs
ce generate-prps prd/product.md

# 5. Validar tudo
ce validate --check-traceability --check-contracts

# 6. Gerar tasks
ce generate-tasks

# 7. Ver status
ce status --detailed

# 8. Ver métricas
ce metrics
```

---

**Version / Versão:** 1.1.0  
**Last Updated / Última Atualização:** 2026-01-07
