# Context Engineer Framework — Complete Technical Overview

> **Version:** 1.0.0 | **Author:** Benjamin Rebello | **License:** MIT | **Python:** >=3.11

---

## Table of Contents

1. [What is Context Engineer](#1-what-is-context-engineer)
2. [The Core Pipeline](#2-the-core-pipeline)
3. [Architecture](#3-architecture)
4. [Core Components](#4-core-components)
5. [CLI Interface](#5-cli-interface)
6. [IDE Integration (Cursor, Windsurf, etc.)](#6-ide-integration)
   - [Global Rules Layer](#61-global-rules-layer)
   - [Specialized Agents](#62-specialized-agents)
   - [Executable Workflows](#63-executable-workflows)
   - [Task Templates](#64-task-templates)
7. [CLI + IDE Complementarity](#7-cli--ide-complementarity)
8. [Token Economy & Cost Reduction](#8-token-economy--cost-reduction)
   - [Context Pruning](#81-context-pruning)
   - [Embedding Cache](#82-embedding-cache)
   - [Pattern Reuse](#83-pattern-reuse)
   - [Confidence Adjustment](#84-confidence-adjustment)
   - [Offline Validation](#85-offline-validation)
9. [Intelligence Modes](#9-intelligence-modes)
10. [AI Governance (Soft-Gate)](#10-ai-governance-soft-gate)
11. [Stack Plugins](#11-stack-plugins)
12. [Validation & Traceability](#12-validation--traceability)
13. [Metrics, ROI & Reporting](#13-metrics-roi--reporting)
14. [Project Configuration](#14-project-configuration)
15. [Production Readiness](#15-production-readiness)
16. [Quick Reference](#16-quick-reference)

---

## 1. What is Context Engineer

Context Engineer is a **framework-agnostic CLI tool** that transforms product ideas into production-ready code through a structured, validated pipeline. It acts as a bridge between business requirements and technical implementation, ensuring full traceability from idea to deployed code.

The framework solves the **context loss problem**: in traditional development, requirements get lost between documents, meetings, and code. Context Engineer creates a **validated chain of artifacts** where every piece of code traces back to a requirement, and every requirement traces forward to implementation.

**Key Principles:**
- **Structured over ad-hoc** — every artifact follows a schema
- **Validated over assumed** — cross-validation at every layer
- **Traceable over disconnected** — PRD ↔ PRPs ↔ Tasks ↔ Commits
- **Offline-first** — works 100% without LLM; AI enhances but is not required

---

## 2. The Core Pipeline

```
Idea → PRD → PRPs (F0-F11) → User Stories → Tasks → Code
```

Each stage produces **validated artifacts** that feed the next:

### Stage 1: Idea → PRD (Product Requirements Document)

The starting point. A product idea is transformed into a structured PRD containing:
- Product vision, market context, target users
- Functional Requirements (FRs) with MoSCoW prioritization
- Non-Functional Requirements (NFRs)
- UX flows, data/privacy considerations, risks
- Acceptance criteria per requirement

**Output:** `PRD.md` (human-readable) + `prd_structured.json` (machine-processable)

```bash
ce generate-prd --interactive   # Guided mode
ce generate-prd idea.md         # From file
ce generate-prd idea.md --preview  # Dry-run
```

### Stage 2: PRD → PRPs (Phase Requirement Plans)

The PRD is decomposed into **incremental phases** (F0 through F11):

| Phase | Purpose |
|-------|---------|
| **F0** | Alignment & Planning (WBS, risks, gates) |
| **F1** | Architecture & Scaffolding (structure, setup, ADRs) |
| **F2** | Data Model & Schemas (entities, migrations, seeds) |
| **F3** | APIs & Contracts (OpenAPI, endpoints, auth, rate limits) |
| **F4** | UX Flows & Screens (happy/edge flows, accessibility, i18n) |
| **F5** | Guided Implementation (TASK files per FR) |
| **F6** | Quality & Testing (lint, unit/integration/contract tests) |
| **F7** | Observability & Analytics (events, metrics, tracing) |
| **F8** | Security & Compliance (STRIDE, LGPD, encryption) |
| **F9** | CI/CD & Rollout (pipelines, feature flags, canary) |

Each PRP contains: objectives, deliverables, inter-phase dependencies, and references to PRD FRs.

**Phase Dependencies (parallelizable):**
```
F0 → F1 → F2, F3, F4 (parallel) → F5 → F6, F7, F8 (parallel) → F9
```

```bash
ce generate-prps                # All phases
ce generate-prps --phase F3     # Single phase
ce generate-prps --parallel     # Parallel generation
```

### Stage 3: PRPs → Tasks

Each phase produces **executable Tasks** — JSON/Markdown artifacts containing:
- Concrete implementation steps
- Artifacts to create (files, endpoints)
- Gherkin test scenarios (Given/When/Then)
- Inter-task dependencies
- Effort estimation (story points)

```bash
ce generate-tasks ./prps
ce generate-tasks --from-us     # From User Story (fast path)
```

### Stage 4: Validation

Cross-validation across all layers:

```bash
ce validate prps/ --prd-file prd.json --tasks-dir tasks/ --api-spec openapi.yaml
```

---

## 3. Architecture

### Project Structure

```
context-engineer/
├── core/                    # Engine (domain + application logic)
│   ├── engine.py            # Main orchestrator (ContextEngine)
│   ├── cache.py             # SQLite cache with semantic search
│   ├── metrics.py           # Metrics collection and ROI tracking
│   ├── validators.py        # Cross-validation (deps, consistency, contracts)
│   ├── planning.py          # Effort estimation with confidence adjustment
│   ├── template_engine.py   # Jinja2 template rendering
│   ├── stack_plugins.py     # Stack plugin management (YAML-based)
│   ├── pattern_library.py   # Reusable code patterns
│   ├── llm_provider.py      # LLM provider management (8 providers)
│   ├── ai_governance_service.py  # AI governance (Soft-Gate)
│   ├── autopilot_service.py # Automated end-to-end pipeline
│   ├── git_service.py       # Git integration with hooks
│   ├── project_analyzer.py  # Project state analysis
│   ├── userstory_integration.py  # US refinement + task generation
│   ├── config_service.py    # Project configuration management
│   ├── logging_service.py   # Structured logging
│   ├── i18n.py              # Internationalization (EN-US / PT-BR)
│   ├── types.py             # TypedDict definitions (PEP 589)
│   └── py.typed             # PEP 561 type-checking marker
├── cli/                     # CLI interface (Click)
│   ├── main.py              # Entry point (ce command)
│   ├── shared.py            # Shared utilities and decorators
│   ├── commands/            # Modular command groups
│   │   ├── generation.py    # init, generate-prd, generate-prps, generate-tasks, validate
│   │   ├── quickstart.py    # 5-minute guided setup
│   │   ├── status.py        # status, checklist, wizard, assist
│   │   ├── reporting.py     # AI efficiency dashboard
│   │   ├── devops.py        # ci-bootstrap, git-setup, install-hooks
│   │   ├── provider.py      # LLM provider configuration
│   │   ├── autopilot.py     # Automated pipeline
│   │   ├── ai_governance.py # Governance commands
│   │   └── ...              # explore, marketplace, patterns, ide, etc.
│   └── py.typed             # PEP 561 marker
├── IDE-rules/               # Context for AI-powered IDEs
│   ├── prompts/             # Agent system prompts
│   ├── workflows/           # Executable phase workflows
│   ├── TASKs/               # Task templates and examples
│   └── docs/                # Raw PRD input
├── templates/               # Jinja2 templates
│   ├── base/                # Project scaffolding templates
│   ├── reporting/           # Dashboard templates (HTML)
│   └── status/              # Status report templates
├── schemas/                 # JSON Schemas (PRP, Task, Stack Plugin)
├── stacks/                  # Stack plugins (YAML)
├── patterns/                # Reusable code patterns (Markdown)
├── metrics/                 # Per-project metrics (JSON)
├── tests/                   # Test suite (pytest)
└── docs/                    # Documentation (bilingual EN/PT-BR)
```

### Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  User       │────▶│  CLI (Click) │────▶│ ContextEngine│
│  (ce ...)   │     │  cli/main.py │     │  core/engine │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                │
                    ┌───────────────────────────┼──────────────────────┐
                    │                           │                      │
              ┌─────▼─────┐  ┌──────────────┐  ┌▼────────────┐  ┌────▼─────┐
              │ Templates │  │ StackPlugins │  │ LLMProvider │  │  Cache   │
              │ (Jinja2)  │  │   (YAML)     │  │ (8 provid.) │  │ (SQLite) │
              └───────────┘  └──────────────┘  └─────────────┘  └──────────┘
```

---

## 4. Core Components

### ContextEngine (`core/engine.py`)

The main orchestrator. Coordinates all other components:

```python
class ContextEngine:
    def __init__(self, templates_dir, patterns_dir, schemas_dir, cache_dir,
                 use_transformers=False, embedding_model=None):
        self.template_engine = TemplateEngine(templates_dir)
        self.pattern_library = PatternLibrary(patterns_dir)
        self.cache = IntelligenceCache(cache_dir, use_transformers, embedding_model)
        self.validator = PRPValidator(schemas_dir)
        self.stack_manager = StackPluginManager(stacks_dir)
        self.metrics = MetricsCollector(metrics_dir)
        # ...
```

**Key methods:** `init_project()`, `generate_prd()`, `generate_prps()`, `generate_tasks()`, `check_dependencies()`

### IntelligenceCache (`core/cache.py`)

SQLite-backed cache with hybrid search (semantic embeddings or Levenshtein fallback):

- **Binary embedding storage** — 90% disk space reduction vs JSON
- **Indexed queries** — 60-80% faster lookups
- **Persistent embedding cache** — avoids recalculating known embeddings (40-60% latency reduction)
- **Pattern success tracking** — patterns ranked by historical success rate

**Tables:** `patterns`, `embeddings`, `token_usage`, `validations`, `metrics`

### PRPValidator (`core/validators.py`)

Cross-validation engine with parallel processing:

- **Dependency validation** — phases don't reference non-existent phases
- **Consistency validation** — PRD FRs are covered in PRPs
- **Traceability validation** — Tasks map back to PRPs and PRD
- **Contract integrity** — API endpoints (F3) match frontend calls (F4)
- **Inverse traceability** — Git commits map back to Tasks
- **Mock server generation** — Prism-based transient mock from OpenAPI spec

### EffortEstimator (`core/planning.py`)

Story point estimation with ML-like local learning:

- **Base calculation** — artifacts, steps, test scenarios, dependencies
- **Stack multiplier** — complexity factor per technology (e.g., Rust 0.7 > Python 0.3)
- **Category multiplier** — complexity per domain (e.g., auth 0.6 > data-models 0.4)
- **Confidence Adjustment** — inflates/deflates based on historical rework rate per category

### MetricsCollector (`core/metrics.py`)

Tracks project health and ROI:

- **Generation metrics** — time, success/failure rate per phase
- **Task metrics** — completion rate, rework rate
- **Quality metrics** — test coverage, code quality score
- **Token metrics** — tokens saved, tokens used, cost savings (USD)
- **Traceability metrics** — tasks with commits, traceability gaps
- **Category rework rates** — per-category rework tracking for confidence adjustment

### Other Components

| Component | File | Purpose |
|-----------|------|---------|
| **TemplateEngine** | `core/template_engine.py` | Jinja2 project scaffolding |
| **StackPluginManager** | `core/stack_plugins.py` | YAML-based stack plugins |
| **PatternLibrary** | `core/pattern_library.py` | Reusable code patterns |
| **LLMProvider** | `core/llm_provider.py` | 8 LLM providers with encrypted credentials |
| **AutopilotService** | `core/autopilot_service.py` | End-to-end automated pipeline |
| **AIGovernanceService** | `core/ai_governance_service.py` | Soft-Gate AI governance |
| **GitService** | `core/git_service.py` | Git integration with hooks |
| **ProjectAnalyzer** | `core/project_analyzer.py` | Project state analysis |
| **UserStoryRefiner** | `core/userstory_integration.py` | FR → User Story refinement |
| **TaskGenerator** | `core/userstory_integration.py` | User Story → Task generation |
| **ReportingService** | `core/reporting_service.py` | Dashboard rendering (HTML/JSON) |

---

## 5. CLI Interface

Entry point: `ce` (installed via `pip install context-engineer`)

### Command Groups

#### Generation Commands
```bash
ce init [PROJECT_NAME] --stack python-fastapi --language en-us
ce generate-prd [INPUT_FILE] --interactive --preview --no-ai
ce generate-prps [PRD_FILE] --phase F3 --parallel --no-ai
ce generate-tasks [PRPS_DIR] --from-us --no-ai
ce validate [PRPS_DIR] --prd-file PRD --tasks-dir TASKS --api-spec OPENAPI
ce check-dependencies [TASKS_DIR]
ce estimate-effort [TASK_FILE] --detailed
ce estimate-batch [TASKS_DIR] --output estimates.json
```

#### Status & Navigation
```bash
ce status [PROJECT_DIR] --json
ce checklist
ce wizard
ce assist
ce quickstart --interactive --example todo-app
```

#### DevOps & Git
```bash
ce ci-bootstrap --provider github
ce git-setup
ce install-hooks
```

#### Reporting & Metrics
```bash
ce report --project-name my-app --format html --output dashboard.html
ce report --stack python-fastapi --format json
```

#### AI & Providers
```bash
ce provider list
ce provider set openai --api-key sk-...
ce ai-governance check
ce ai-governance policy
```

#### Exploration
```bash
ce explore patterns
ce explore stacks
ce marketplace search auth
```

### Shared Options

All generation commands support:
- `--no-ai` / `--ai` — disable/enable LLM intelligence
- `--embedding-model MODEL` — select embedding model
- `--verbose` / `--quiet` / `--log-level LEVEL` — logging control

---

## 6. IDE Integration

Context Engineer is designed to work **inside AI-powered IDEs** (Cursor, Windsurf, Copilot) as a structured context provider. The IDE's AI reads the framework's artifacts and follows its rules automatically.

### 6.1 Global Rules Layer

Files in `IDE-rules/prompts/` act as **permanent system prompts** for the IDE's AI:

#### `AGENTS.md` — Behavioral Rules
```markdown
- Explanations follow user-selected language (EN-US or PT-BR)
- Code comments and docstrings: EN-US only
- Budgets: API p95 ≤ 200ms; frontend bundle ≤ 250KB
- Privacy/LGPD: no PII in logs, retention documented
- Mandatory test coverage: unit, integration, contract suites
- Always produce complete diffs and a changelog
```

#### `GLOBAL_ENGINEERING_RULES.json` — 20 Prioritized Rules

20 rules with priority levels (`critical` > `high` > `medium`):

| # | Priority | Rule |
|---|----------|------|
| 1 | critical | Adhere to existing architecture and conventions |
| 2 | critical | Semantic search before generating new code |
| 3 | high | DRY: extract repeated logic into reusable abstractions |
| 4 | high | SOLID + Clean Architecture (domain/app/infra/interfaces) |
| 5 | high | TDD workflow: fail → pass → refactor |
| 6 | high | BDD workflow: Gherkin → step definitions → logic |
| 7 | critical | Technology consistency (only use existing stack) |
| 8 | medium | Document all public functions (docstrings/JSDoc) |
| 9 | high | Provide technical changelog after every change |
| 10 | medium | Proactively suggest refactors for code smells |
| 11 | high | Conventional Commits format |
| 12 | critical | Communication in Brazilian Portuguese |
| 13 | critical | Code documentation in English |
| 14-20 | varies | Structure preservation, codebase search, reuse, organization |

#### `PROJECT_STANDARDS.md` — Adaptive Standards

Standards that **adapt to the selected stack plugin**:
- Clean Architecture structure (mandatory)
- Quality gates (pre-commit, pre-merge)
- Performance budgets (customizable per project)
- Security & compliance (LGPD/GDPR)
- Observability (JSON logs, OpenTelemetry)
- Commit conventions (Conventional Commits)

### 6.2 Specialized Agents

Four agent system prompts, each with a detailed role:

| Agent | File | Role | When to Use |
|-------|------|------|-------------|
| **360° PRD Agent** | `Agente_PRD_360.md` | Product Manager + Engineer | Creating PRDs from ideas |
| **PRP Orchestrator** | `Agente_PRP_Orquestrador.md` | Software Architect | Decomposing PRD into phases |
| **Direct Task Agent** | `Agente_Task_Direto.md` | Senior Engineer | User Story → Code (fast path) |
| **User Story Refiner** | `Agente_UserStory_Refiner.md` | Product Owner | Refining FRs into testable stories |

**Usage in IDE:** Reference the agent via `@` mention or paste its prompt:

```
@Agente_Task_Direto.md

User Story:
As an authenticated user
I want to log out
So that my session ends securely
```

The IDE's AI then:
1. Searches the existing codebase
2. Generates `TASK.US-001.md` + `TASK.US-001.json`
3. Implements code following Clean Architecture
4. Generates BDD tests (Gherkin → step definitions)
5. Runs validations (`pytest`, `ruff check`)
6. Iterates until all checks pass

### 6.3 Executable Workflows

`IDE-rules/workflows/` contains **numbered workflows** (F0-F11) that the AI follows sequentially:

```
00_global_rules.md      → Gate: validate rules before anything
01_prd_optimizer.md     → Convert raw PRD → 360° PRD + JSON
02_prp_compiler.md      → Compile PRPs from PRD
03_plan.md/.json        → Planning (WBS, risks)
04_scaffold.md/.json    → Architecture + scaffolding
05_data_model.md/.json  → Data model + migrations
06_api_contracts.md/.json → APIs + OpenAPI + contracts
07_ux_flows.md/.json    → UX flows + wireframes
08_quality.md/.json     → Tests + quality gates
09_observability.md/.json → Logs + tracing + metrics
10_security.md/.json    → LGPD + threat model + secrets
11_ci_cd_rollout.md/.json → Pipeline + deploy + rollback
```

Each workflow is a **runbook**: load context → act → validate → refine.

### 6.4 Task Templates

`IDE-rules/TASKs/` contains reference templates:

```
TASK.FR-001.json         → Example Task (JSON)
TASK.FR-001.md           → Example Task (Markdown)
TASK.US-template.json    → User Story Task template
TASK.US-template.md      → User Story Task template
```

---

## 7. CLI + IDE Complementarity

The CLI and IDE AI serve **different but complementary roles**:

| Aspect | CLI (`ce ...`) | IDE AI (Cursor/Windsurf) |
|--------|---------------|--------------------------|
| **Executor** | Python framework | IDE's LLM |
| **Context** | Jinja2 templates + heuristics | System prompts + agents + workflows |
| **Generation** | Deterministic (templates) or LLM | Always via IDE's LLM |
| **Validation** | `ce validate` (automatic) | AI follows workflow checklist |
| **Artifacts** | PRD, PRPs, Tasks (same format) | PRD, PRPs, Tasks (same format) |
| **Token cost** | Zero (offline) or minimal | Optimized via curated context |

**The key insight:** artifacts are **format-compatible**. Whether generated via `ce generate-prps` or by asking Cursor to follow `@Agente_PRP_Orquestrador.md`, the output is the same format, validatable by the same `ce validate`.

### The Complete Cycle

```
                CLI (0 tokens)              IDE (optimized tokens)
                ─────────────               ──────────────────────

1. SCAFFOLDING  ce init my-app
                → Structure, templates,
                configs (Jinja2, zero LLM)

2. PRD          ce generate-prd             AI refines PRD using
                --interactive               @Agente_PRD_360.md
                → Captures inputs           → Context: agent prompt
                → Validates fields          + inputs (~3K tokens
                → Generates structured JSON vs ~20K without CE)

3. PRPs         ce generate-prps            AI details each phase
                → Template per phase        using @Agente_PRP
                → Validates dependencies    → Context: PRD + current
                → Detects gaps              phase (~5K vs ~40K)

4. VALIDATION   ce validate
                → Consistency PRD↔PRPs      (ZERO tokens — fully
                → Inter-phase dependencies  deterministic)
                → API↔Frontend contracts

5. TASKS        ce generate-tasks           AI implements each Task
                → Estimates story points    using @Agente_Task
                → Searches similar patterns → Context: 1 Task +
                → Applies confidence adj.   similar pattern (~2K
                                            vs ~15K per task)

6. IMPLEMENTATION                           AI implements with
                                            complete Task: steps,
                                            diffs, tests, validations

7. VERIFICATION ce validate
                → Traceability              (ZERO tokens)
                → Contracts
                → Test coverage

8. METRICS      ce report
                → ROI (tokens saved/used)   (ZERO tokens)
                → Rework rate per category
                → Confidence adjustment
```

---

## 8. Token Economy & Cost Reduction

### 8.1 Context Pruning

Without the framework, the IDE AI reads the **entire codebase** to understand context:

```
Without CE:  "Implement login" → AI reads 50 files → ~80,000 context tokens
With CE:     "Implement TASK.FR-001" → AI reads 1 Task + 1 PRP → ~3,000 tokens
```

The Task already contains everything the AI needs: objective, steps, expected diffs, Gherkin tests, and validations. The `MetricsCollector` tracks this:

```python
# core/metrics.py — ProjectMetrics
tokens_saved: int = 0           # Total tokens saved via Context Pruning
tokens_used: int = 0            # Total tokens used
context_pruning_events: int = 0 # How many times pruning was applied
estimated_cost_saved_usd: float # Estimated savings in USD
```

### 8.2 Embedding Cache

`IntelligenceCache` stores embeddings in **SQLite with binary cache**:

1. Check if embedding exists in SQLite cache
2. If yes: return directly (0 tokens, ~1ms)
3. If no: generate, store, return

Binary storage (`np.float32.tobytes()`) reduces disk space by **90%** vs JSON. Repeated queries see **40-60% latency reduction**.

### 8.3 Pattern Reuse

`PatternLibrary` + `IntelligenceCache` maintain a bank of **reusable code patterns** with success rates:

```python
@dataclass
class CodePattern:
    pattern_id: str
    code: str              # Pattern code
    metadata: dict         # Stack, category, tags
    success_rate: float    # Historical success rate (0.0-1.0)
    usage_count: int       # Times used
```

Search uses two modes:
- **Semantic** (with transformers): embedding → cosine similarity → ranked patterns
- **Levenshtein** (offline, zero tokens): text similarity → fallback

```
Without CE:  AI generates from scratch → ~2,000 output tokens + possible rework
With CE:     AI receives 95%-success pattern → adapts → ~400 output tokens
```

### 8.4 Confidence Adjustment

`EffortEstimator` implements **local learning** that reduces rework (and therefore tokens spent on iterations):

```python
# core/planning.py — If "security" tasks always have 30% rework:
#   → Inflate estimate by 30% for future security tasks
#   → AI receives more security context preventively
#   → Fewer "this isn't secure, redo it" iterations
```

`MetricsCollector` tracks **rework per category**:
```python
category_rework_rates = {"security": {"total": 10, "rework": 3, "rate": 0.3}}
```

### 8.5 Offline Validation

The biggest savings come from **deterministic validation** without LLM:

```bash
ce validate prps/ --prd-file prd.json --tasks-dir tasks/ --api-spec openapi.yaml
```

| Validation | What it detects | Tokens saved |
|------------|-----------------|--------------|
| **Dependencies** | Phase references non-existent phase | Prevents AI from generating code for broken phase |
| **Consistency** | PRD FR not covered in PRPs | Prevents AI from implementing incomplete feature |
| **Traceability** | Task without PRD/PRP link | Prevents AI from losing requirement context |
| **Contracts** | Frontend calls non-existent API endpoint | Prevents AI from generating broken integration |
| **Inverse** | Commit without associated Task | Detects "loose" code without requirement |

### Estimated Savings

| Metric | Without CE | With CE | Savings |
|--------|-----------|---------|---------|
| Tokens per feature | ~500K | ~150K | **~70%** |
| Rework iterations | 3-5 | 0-1 | **~80%** |
| Context per prompt | 50+ files | 1-3 artifacts | **~95%** |
| Validation tokens | Manual (LLM) | Automatic (CLI) | **100%** |

---

## 9. Intelligence Modes

The framework operates in **two modes**:

### Offline Mode (`--no-ai`)
- 100% offline, zero LLM tokens
- Jinja2 templates for generation
- Levenshtein similarity for pattern search
- Local heuristics for effort estimation
- Full validation suite

### AI-Enhanced Mode (`--ai`)
- LLM providers for richer content generation
- Semantic search via sentence-transformers embeddings
- Model: `all-MiniLM-L6-v2` (default, configurable)
- API keys stored encrypted via `_CredentialVault`

**Supported LLM Providers:** OpenAI, Google Gemini, Anthropic Claude, Groq, Ollama, Azure OpenAI, Mistral, Cohere

---

## 10. AI Governance (Soft-Gate)

`AIGovernanceService` implements a governance model:

- **Dependency checking** — verifies transformer availability before enabling AI
- **Preference resolution** — CLI flags > project config > environment variables
- **Model normalization** — friendly aliases mapped to canonical identifiers
- **Policy versioning** — `AI_GOVERNANCE_POLICY_VERSION` env var for compliance
- **Soft-Gate mode** — advisory warnings vs hard-blocking errors

```bash
ce ai-governance check    # Check AI readiness
ce ai-governance policy   # View/set governance policy
```

---

## 11. Stack Plugins

YAML-based plugins in `stacks/` that adapt the framework to any technology:

### Available Stacks

| Stack | File | Description |
|-------|------|-------------|
| `python-fastapi` | `stacks/python-fastapi.yaml` | Python 3.11+ with FastAPI, SQLModel |
| `node-react` | `stacks/node-react.yaml` | Node.js 20+ with React, TypeScript, Vite |
| `go-gin` | `stacks/go-gin.yaml` | Go with Gin framework, GORM |
| `vue3` | `stacks/vue3.yaml` | Vue 3 with Composition API, TypeScript |

### Plugin Structure

```yaml
name: "python-fastapi"
version: "1.0.0"
commands:
  init: "uv venv && uv pip install fastapi uvicorn"
  install: "pip install"
  test: "pytest -v"
  lint: "ruff check ."
  format: "black ."
  type_check: "mypy ."
structure:
  domain: "src/domain"
  application: "src/application"
  infrastructure: "src/infrastructure"
  interfaces: "src/interfaces"
patterns:
  - "patterns/api-patterns/restful-crud.md"
  - "patterns/authentication/jwt-fastapi.md"
dependencies:
  - "fastapi>=0.100.0"
  - "sqlmodel>=0.0.8"
```

### Custom Stacks

Create `stacks/python-django.yaml` and use: `ce init my-project --stack python-django`

---

## 12. Validation & Traceability

### Validation Types

```bash
# Basic validation (dependencies + structure)
ce validate ./prps

# With PRD consistency check
ce validate ./prps --prd-file prd/prd_structured.json

# Full traceability (PRD → PRPs → Tasks)
ce validate ./prps --prd-file prd.json --tasks-dir tasks/

# Contract integrity (API ↔ Frontend)
ce validate ./prps --api-spec openapi.yaml --ui-tasks-dir tasks/

# Inverse traceability (Tasks → Commits)
ce validate ./prps --tasks-dir tasks/ --commits-json commits.json

# Dry-run (show what would be validated)
ce validate ./prps --dry-run

# Soft-check (warnings only, no abort)
ce validate ./prps --soft-check
```

### Contract Integrity (Deep Cross-Validation)

Validates that UI tasks (F4) match the OpenAPI spec from F3:
- Detects **broken contracts** when API changes invalidate UI implementations
- Matches HTTP method + path patterns (including path parameters)
- Matches `fetch()` calls in task code against spec endpoints
- Uses **parallel processing** (`ThreadPoolExecutor`) for performance

### Mock Server Generation

```python
validator.generate_transient_mock(openapi_spec, port=4010)
# → Starts Prism mock server from OpenAPI spec
# → AI agent can test UI against mock during development
```

---

## 13. Metrics, ROI & Reporting

### ProjectMetrics

```python
@dataclass
class ProjectMetrics:
    project_name: str
    prp_generation_time_minutes: float
    total_phase_generations: int
    failed_phase_generations: int
    phase_failure_rate: float
    task_completion_rate: float
    test_coverage_achieved: float
    code_quality_score: float
    rework_rate: float
    tokens_saved: int
    tokens_used: int
    context_pruning_events: int
    estimated_cost_saved_usd: float
    category_rework_rates: dict  # Per-category rework tracking
    phase_generation_stats: dict  # Per-phase timing and success
```

### ROI Tracking

```python
# Record context pruning event
metrics.record_context_pruning(project_name, tokens_saved=5000, cost_saved=0.15)

# Get ROI metrics
roi = metrics.get_roi_metrics(project_name)
# → {"tokens_saved": 50000, "tokens_used": 15000, "savings_percentage": 333.3,
#    "estimated_cost_saved_usd": 2.85, "context_pruning_events": 12}
```

### Dashboards

```bash
ce report --project-name my-app --format html --output dashboard.html
ce report --format json
ce report --stack python-fastapi
```

Rendered via Jinja2 templates (`templates/reporting/`):
- `project_dashboard.html.j2` — single project view
- `global_dashboard.html.j2` — cross-project aggregation

---

## 14. Project Configuration

### `.ce-config.json`

Per-project configuration file:

```json
{
  "project_name": "my-api",
  "stack": "python-fastapi",
  "language": "en-us",
  "use_transformers": true,
  "embedding_model": "all-MiniLM-L6-v2",
  "custom_commands": {
    "test": "pytest -v --cov --cov-report=html",
    "lint": "ruff check . --fix"
  },
  "quality_overrides": {
    "min_coverage": 85,
    "max_complexity": 10
  },
  "performance_budgets": {
    "api_p95_ms": 150,
    "bundle_size_kb": 200
  }
}
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `CONTEXT_ENGINEER_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `AI_GOVERNANCE_POLICY_VERSION` | Governance policy version for compliance |
| `CE_LLM_PROVIDER` | Default LLM provider |
| `CE_LLM_API_KEY` | LLM API key (alternative to `ce provider set`) |

---

## 15. Production Readiness

### Current Status (v1.0.0)

| Metric | Value |
|--------|-------|
| **Tests** | 716 passing, 0 failing |
| **Coverage** | 93% (4,832 statements, 335 missing) |
| **Linting** | ruff — all checks passed |
| **Formatting** | black — all formatted |
| **Type Safety** | PEP 561 markers (`py.typed`) in `core/` and `cli/` |
| **CI/CD** | GitHub Actions (test matrix, lint, type-check, package build) |
| **Version** | Unified `1.0.0` (single source of truth in `core/__init__.py`) |

### CI/CD Pipeline (`.github/workflows/ci.yml`)

| Job | Description |
|-----|-------------|
| **test** | Matrix (Python 3.11, 3.12), pytest with coverage, artifact upload |
| **lint** | ruff check + black check |
| **type-check** | mypy with `--ignore-missing-imports` |
| **package** | Build wheel, install, verify `ce --version` |

### Quality Configuration (`pyproject.toml`)

```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.black]
line-length = 120
target-version = ["py311"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --tb=short"
```

---

## 16. Quick Reference

### 5-Minute Quickstart

```bash
pip install context-engineer
ce quickstart --interactive
```

### Typical Workflow

```bash
# 1. Initialize project
ce init my-app --stack python-fastapi

# 2. Generate PRD
ce generate-prd --interactive

# 3. Generate PRPs
ce generate-prps prd/prd_structured.json

# 4. Validate
ce validate prps/ --prd-file prd/prd_structured.json

# 5. Generate Tasks
ce generate-tasks prps/

# 6. Estimate effort
ce estimate-batch tasks/

# 7. Check status
ce status

# 8. View metrics
ce report --format html --output dashboard.html
```

### Fast Path (User Story → Code)

```bash
ce generate-tasks --from-us
# → Interactive: provide User Story + acceptance criteria
# → Generates TASK.US-XXX.md + .json
# → Ready for implementation
```

### IDE Integration

1. Open project in Cursor/Windsurf
2. IDE reads `IDE-rules/prompts/` automatically
3. Reference agents: `@Agente_PRD_360.md`, `@Agente_Task_Direto.md`, etc.
4. AI follows structured workflows with curated context
5. Validate results: `ce validate`

---

> **Context Engineer** — Transforming ideas into production-ready code through structured, validated, and traceable engineering.
