# Índice - Context Engineer

> **Language Navigation / Navegação**
> - [English Reference](#documentação-principal)
> - [Referência em Português](#documentação-principal)
>
> **Language note:** `@Agente_PRD_360.md` asks which language to use (EN-US or PT-BR) before generating the PRD. Keep bilingual documentation handy to mirror the user’s preference.

## Documentação Principal

### Para Começar (Leia nesta ordem):

1. **[README.md](README.md)** - Visão geral e início rápido *(bilingual navigation)*
2. **[MAIN_USAGE_GUIDE.md](MAIN_USAGE_GUIDE.md)** **COMECE AQUI** - Guia completo passo a passo *(bilingual navigation)*
3. **[USER_STORY_QUICK_GUIDE.md](USER_STORY_QUICK_GUIDE.md)** **RÁPIDO** - Uso direto com UserStory (1 passo) *(bilingual navigation)*
> **Language note:** `@Agente_PRD_360.md` asks for EN-US or PT-BR before generating the PRD. Keep bilingual documentation handy so you can mirror the user’s preferred language.
 *(bilingual navigation)*
4. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Referência rápida de comandos *(bilingual navigation)*

### Documentação Técnica:

4. **[PRP_BUSINESS_RULES.md](PRP_BUSINESS_RULES.md)** - Regras detalhadas dos PRPs e Context Engineering *(bilingual navigation)*
5. **[IDE_EXAMPLES.md](IDE_EXAMPLES.md)** - Exemplos práticos por domínio (E-commerce, Hospitalar, etc.)
6. **[MULTI_IDE_USAGE_GUIDE.md](MULTI_IDE_USAGE_GUIDE.md)** - Uso em outras IDEs e sem IA *(bilingual navigation)*

---

## Matriz Documento × Propósito / Document × Purpose Matrix

| Documento / Document | Propósito (PT-BR) / Purpose (EN) | Comandos principais / Key commands | Referências de código / Code references |
| --- | --- | --- | --- |
| README.md | Visão geral do framework / Framework overview | `ce quickstart`, `ce init` | `cli/main.py`, `cli/commands/quickstart.py` |
| MAIN_USAGE_GUIDE.md | Passo a passo completo / Full step-by-step flow | `ce init`, `ce generate-prd`, `ce generate-prps`, `ce generate-tasks`, `ce validate` | `cli/commands/generation.py`, `core/autopilot_service.py` |
| QUICK_REFERENCE.md | Cola de comandos / Command cheatsheet | `ce assist`, `ce status`, `ce wizard`, `ce autopilot`, `ce patterns list` | `cli/commands/status.py`, `cli/commands/autopilot.py`, `cli/commands/patterns.py` |
| USER_STORY_QUICK_GUIDE.md | Fluxo direto por User Story / Direct User Story flow | `@Agente_Task_Direto.md`, `ce generate-tasks --from-us` | `cli/commands/generation.py` (`generate_tasks`), `core/engine.py` |
| CLI_COMMANDS.md | Manual detalhado da CLI / Detailed CLI manual | `ce --help`, todos os subcomandos | `cli/main.py`, `cli/commands/*` |
| PRP_BUSINESS_RULES.md | Regras e fases dos PRPs / PRP phase rules | `ce generate-prps`, `ce validate --soft-check` | `cli/commands/generation.py`, `core/engine.py`, `core/validators.py` |
| AI_GOVERNANCE.md | Soft-Gate e políticas de IA / AI governance policies | `ce ai-governance status`, `ce doctor`, `ce checklist` | `cli/commands/ai_governance.py`, `cli/commands/doctor.py`, `cli/commands/status.py`, `core/ai_governance_service.py` |
| MULTI_IDE_USAGE_GUIDE.md | Uso em múltiplas IDEs / Multi-IDE usage | `ce ide sync`, `ce assist`, `ce wizard` | `cli/commands/ide.py`, `cli/commands/status.py` |
| MARKETPLACE.md | Instalação de aceleradores / Installing accelerators | `ce marketplace list`, `ce marketplace install` | `cli/commands/marketplace.py`, `core/marketplace_service.py` |
| NEW_STACK_ONBOARDING_GUIDE.md | Criação de novas stacks / Adding new stacks | `ce init --stack`, `ce ide sync` | `stacks/*.yaml`, `cli/commands/generation.py` (`init`) |
| DASHBOARD.md | Relatórios e dashboards / Reports and dashboards | `ce report`, `ce metrics-summary`, `ce ai-status` | `cli/commands/reporting.py`, `core/reporting_service.py`, `templates/reporting/*.j2` |

> **Como usar / How to use:** Localize rapidamente o documento certo, execute os comandos indicados e abra os módulos Python correspondentes para entender ou estender o comportamento.

---

## Mapeamento Detalhado: Comandos CLI × Implementação

### Comandos de Geração (Pipeline Principal)

| Comando | Flags Principais | Serviço Core | Arquivo CLI |
|---------|------------------|--------------|-------------|
| `ce init` | `--template`, `--stack`, `--git-hooks`, `--language`, `--ai/--no-ai`, `--embedding-model` | `core/engine.py` (`init_project`) | `cli/commands/generation.py` |
| `ce generate-prd` | `--input-file`, `--output`, `--interactive`, `--ai/--no-ai`, `--embedding-model` | `core/engine.py` (`generate_prd`) | `cli/commands/generation.py` |
| `ce generate-prps` | `--prd-file`, `--output`, `--parallel`, `--interactive`, `--ai/--no-ai`, `--embedding-model` | `core/engine.py` (`generate_prps`) | `cli/commands/generation.py` |
| `ce generate-tasks` | `--prps-dir`, `--output`, `--from-us`, `--interactive`, `--ai/--no-ai`, `--embedding-model` | `core/engine.py` (`generate_tasks`) | `cli/commands/generation.py` |
| `ce validate` | `--prd-file`, `--tasks-dir`, `--soft-check`, `--commits-json`, `--project-name` | `core/validators.py` (`PRPValidator`) | `cli/commands/generation.py` |

### Comandos de Assistência e Status

| Comando | Flags Principais | Serviço Core | Arquivo CLI |
|---------|------------------|--------------|-------------|
| `ce status` | `--project-dir`, `--json`, `--ai/--no-ai`, `--embedding-model` | `core/project_status_service.py` | `cli/commands/status.py` |
| `ce checklist` | `--project-dir` | `core/project_status_service.py` | `cli/commands/status.py` |
| `ce assist` | `--project-dir`, `--format`, `--output-file`, `--open`, `--ai/--no-ai`, `--embedding-model` | `core/project_status_service.py` | `cli/commands/status.py` |
| `ce wizard` | `--project-dir`, `--ai/--no-ai`, `--embedding-model` | `core/project_status_service.py` | `cli/commands/status.py` |
| `ce autopilot` | `--project-dir`, `--project-name`, `--stack`, `--idea-file`, `--prd-file`, `--prps-dir`, `--tasks-dir`, `--skip-validate`, `--tasks-from-us`, `--ai/--no-ai`, `--embedding-model` | `core/autopilot_service.py` | `cli/commands/autopilot.py` |

### Comandos de Governança e Diagnóstico

| Comando | Flags Principais | Serviço Core | Arquivo CLI |
|---------|------------------|--------------|-------------|
| `ce ai-governance status` | `--project-dir`, `--format` | `core/ai_governance_service.py` | `cli/commands/ai_governance.py` |
| `ce doctor` | `--project-dir`, `--format`, `--ai-profile` | `core/ai_governance_service.py`, `core/config_service.py` | `cli/commands/doctor.py` |
| `ce report` | `--project-name`, `--output`, `--format` | `core/reporting_service.py`, `core/metrics.py` | `cli/commands/reporting.py` |
| `ce metrics-summary` | `--project-name`, `--tasks-dir` | `core/metrics.py` | `cli/commands/reporting.py` |
| `ce ai-status` | `--project-dir`, `--format` | `core/ai_governance_service.py` | `cli/commands/reporting.py` |

### Comandos de Marketplace e Padrões

| Comando | Flags Principais | Serviço Core | Arquivo CLI |
|---------|------------------|--------------|-------------|
| `ce marketplace list` | `--category`, `--stack` | `core/marketplace_service.py` | `cli/commands/marketplace.py` |
| `ce marketplace install` | `<item_id>`, `--project-dir` | `core/marketplace_service.py` | `cli/commands/marketplace.py` |
| `ce patterns list` | `--stack`, `--category` | `core/engine.py` (`pattern_library`) | `cli/commands/patterns.py` |
| `ce patterns show` | `<pattern_id>` | `core/engine.py` (`pattern_library`) | `cli/commands/patterns.py` |
| `ce patterns suggest` | `--project-dir`, `--ai/--no-ai`, `--embedding-model` | `core/engine.py` (`pattern_library`), `core/cache.py` | `cli/commands/patterns.py` |

### Comandos DevOps e Utilidades

| Comando | Flags Principais | Serviço Core | Arquivo CLI |
|---------|------------------|--------------|-------------|
| `ce install-hooks` | `--project-dir`, `--hard-gate` | `core/git_service.py` (`GitHookManager`) | `cli/commands/devops.py` |
| `ce ci-bootstrap` | `--project-dir`, `--platform` | `core/git_service.py` | `cli/commands/devops.py` |
| `ce ide sync` | `--project-dir` | N/A (copia arquivos) | `cli/commands/ide.py` |
| `ce alias` | `<subcommand>` | N/A (gerencia aliases) | `cli/commands/alias.py` |

> **Nota importante:** Todos os comandos que aceitam `--ai/--no-ai` e `--embedding-model` utilizam o `AIGovernanceService` (`core/ai_governance_service.py`) para resolver preferências de IA e modelos de embedding.

---

## Estrutura de Pastas

### Pastas Principais:

```
context-engineer/
├── .ide-rules/ # Copie para seu projeto como .{nome da sua ide}/
│ ├── prompts/ # Prompts dos agentes de IA
│ │ ├── Agente_PRD_360.md # Gera PRD
│ │ ├── Agente_PRP_Orquestrador.md # Gera PRPs
│ │ ├── Agente_UserStory_Refiner.md # Refina UserStories
│ │ ├── GLOBAL_ENGINEERING_RULES.json # Regras globais
│ │ ├── PROJECT_STANDARDS.md # Stack tecnológica
│ │ └── AGENTS.md # Configurações
│ └── workflows/ # Templates de workflows por fase
│ ├── 03_plan.md/.json # F0 - Planejamento
│ ├── 04_scaffold.md/.json # F1 - Estrutura
│ └── ... (F2-F8)
│
├── core/ # Framework reutilizável (Python)
├── cli/ # CLI tool (opcional)
├── templates/ # Templates parametrizáveis
├── patterns/ # Biblioteca de padrões
├── stacks/ # Plugins de stack
└── schemas/ # JSON Schemas para validação
```

---

## Fluxo de Uso

### 1. Setup Inicial
```bash
# Copie IDE-rules para .ide-rules no seu projeto
cp -r IDE-rules .ide-rules

# Configure regras
code .ide-rules/prompts/GLOBAL_ENGINEERING_RULES.json
code .ide-rules/prompts/PROJECT_STANDARDS.md
```

### 2. Gerar PRD
```
# No IDE, use:
@Agente_PRD_360.md
Faça o processo descrito para a ideia: [sua ideia]
```

### 3. Gerar PRPs
```
# No IDE, use:
@Agente_PRP_Orquestrador.md
Faça o processo descrito usando: @prd_structured.json
```

### 4. Implementar Tasks
```
# No IDE, use:
@TASKs/TASK.FR-001.md
Execute a task descrita acima.
```

---

## Documentos por Perfil

### **Iniciante**:
1. README.md *(bilingual)*
2. MAIN_USAGE_GUIDE.md *(bilingual)*
3. QUICK_REFERENCE.md *(bilingual)*

### **Desenvolvedor**:
1. MAIN_USAGE_GUIDE.md (Passo 3) *(bilingual)*
2. QUICK_REFERENCE.md *(bilingual)*
3. IDE_EXAMPLES.md *(bilingual header)*

### **Arquiteto**:
1. PRP_BUSINESS_RULES.md *(bilingual)*
2. MAIN_USAGE_GUIDE.md (Passo 2) *(bilingual)*
3. IDE_EXAMPLES.md *(bilingual header)*

### **Product Manager**:
1. MAIN_USAGE_GUIDE.md (Passo 1) *(bilingual)*
2. IDE_EXAMPLES.md *(bilingual header)*
3. PRP_BUSINESS_RULES.md *(bilingual)*

---

## Busca Rápida

### **Setup e Configuração**:
- MAIN_USAGE_GUIDE.md (Passo 0)
- `.ide-rules/prompts/GLOBAL_ENGINEERING_RULES.json`
- `.ide-rules/prompts/PROJECT_STANDARDS.md`

### **Geração de PRD**:
- MAIN_USAGE_GUIDE.md (Passo 1)
- `.ide-rules/prompts/Agente_PRD_360.md`

### **Geração de PRPs**:
- MAIN_USAGE_GUIDE.md (Passo 2)
- `.ide-rules/prompts/Agente_PRP_Orquestrador.md`
- PRP_BUSINESS_RULES.md

### **Implementação**:
- MAIN_USAGE_GUIDE.md (Passo 3)
- QUICK_REFERENCE.md
- IDE_EXAMPLES.md

### **Comandos e Referência**:
- QUICK_REFERENCE.md
- MAIN_USAGE_GUIDE.md (seção Comandos Úteis)

---

## Documentos de Análise (Opcional)

Documentos técnicos sobre implementação e melhorias estão em:
- `docs/analise/` - Análises técnicas e implementações
- `docs/MELHORIAS_NIVEL_SENIOR.md` - Melhorias de nível sênior (Context Pruning, Deep Cross-Validation)
- `docs/REFINAMENTOS_FINAIS.md` - Refinamentos DevOps (Git Hooks, Mock Server, Confidence Adjustment)
- `docs/NEW_STACK_ONBOARDING_GUIDE.md` - Como adicionar sua própria stack
- `docs/AI_GOVERNANCE.md` - Sistema de Governança de IA (Soft-Gate, ROI Tracking)

---

## Stacks e Padrões Disponíveis

### Stacks Suportadas

Localização: `stacks/*.yaml`

| Stack | Arquivo | Tecnologias Principais | Comandos de Validação |
|-------|---------|------------------------|----------------------|
| **Python FastAPI** | `python-fastapi.yaml` | Python 3.11+, FastAPI, SQLModel, PyTest | `pytest -q`, `ruff check .`, `black --check .` |
| **Node React** | `node-react.yaml` | Node 20+, React, TypeScript, Vite, Tailwind | `npm run lint`, `npm run test`, `npm run build` |
| **Go Gin** | `go-gin.yaml` | Go 1.21+, Gin, GORM | `go test ./...`, `golangci-lint run` |
| **Vue 3** | `vue3.yaml` | Vue 3, TypeScript, Pinia, Vite, Tailwind | `npm run lint`, `npm run test:unit`, `npm run build` |

**Como usar:** `ce init my-project --stack python-fastapi`

**Adicionar nova stack:** Consulte `docs/NEW_STACK_ONBOARDING_GUIDE.md` e crie um arquivo YAML em `stacks/` seguindo o schema em `schemas/stack_plugin.schema.yaml`.

### Biblioteca de Padrões

Localização: `patterns/`

| Categoria | Padrões Disponíveis | Localização |
|-----------|---------------------|-------------|
| **API Patterns** | RESTful CRUD | `patterns/api-patterns/restful-crud.md` |
| **Authentication** | JWT FastAPI | `patterns/authentication/jwt-fastapi.md` |

**Como usar:**
```bash
# Listar padrões disponíveis
ce patterns list --stack python-fastapi

# Ver detalhes de um padrão
ce patterns show AUTH.JWT

# Sugerir padrões baseado no projeto atual
ce patterns suggest --project-dir .
```

**Adicionar novo padrão:** Crie um arquivo Markdown em `patterns/<categoria>/` e atualize `docs/marketplace_catalog.json` para disponibilizá-lo via marketplace.

---

## Checklist de Início

### Para Iniciantes
- [ ] README.md (bilingual) – visão geral
- [ ] MAIN_USAGE_GUIDE.md (bilingual) – fluxo completo
- [ ] USER_STORY_QUICK_GUIDE.md (bilingual) – fluxo rápido
- [ ] QUICK_REFERENCE.md (bilingual) – comandos essenciais

### Para Desenvolvedores
- [ ] CLI_COMMANDS.md – referência completa de comandos
- [ ] PRP_BUSINESS_RULES.md (bilingual) – regras de negócio
- [ ] MULTI_IDE_USAGE_GUIDE.md (bilingual) – uso em diferentes IDEs

### Para Arquitetos e Tech Leads
- [ ] AI_GOVERNANCE.md (bilingual) – governança e políticas
- [ ] DASHBOARD.md – métricas e relatórios
- [ ] MARKETPLACE.md – aceleradores disponíveis
- [ ] NEW_STACK_ONBOARDING_GUIDE.md (bilingual) – adicionar stacks customizadas

### Documentação Técnica Avançada
- [ ] MELHORIAS_NIVEL_SENIOR.md – Context Pruning, Deep Cross-Validation
- [ ] REFINAMENTOS_FINAIS.md – Git Hooks, Mock Server, Confidence Adjustment

---

**Dica**: Comece sempre pelo **[MAIN_USAGE_GUIDE.md](MAIN_USAGE_GUIDE.md)** para o processo completo passo a passo!
