# Context Engineer - Uso em Múltiplas IDEs e Sem IA

> **Language Navigation / Navegação**
> - [English Reference](#english-reference)
> - [Referência em Português](#referencia-em-portugues)
>
> **Language note:** `@Agente_PRD_360.md` asks which language to use (EN-US or PT-BR) before generating PRD content. Keep bilingual inputs ready so IDE agents and the CLI can mirror the preferred language.

## English Reference

### 1. Overview

This playbook shows how to operate Context Engineer in any IDE (Cursor, VS Code + Copilot, JetBrains AI, Windsurf, Antigravity, etc.) and how to fall back to a CLI-only workflow when AI copilots are not available. The logical correlations between prompts, CLI commands, governance hooks and dashboards are mapped in `docs/assets/context_engineer_flow.mmd`. If your environment cannot render Mermaid, use the pre-generated PNG at `docs/assets/context_engineer_flow.png`.

### 2. Terminal interaction tracks

| Track | Command(s) | When to use |
|-------|------------|-------------|
| **Conversational assistant** | `ce assist --format text`, `ce assist --format html --open` | Combines project inspection, pattern/cache hints and inline execution (`ce init`, `ce generate-prd`, `ce generate-prps`, `ce generate-tasks`), ideal when pairing with copilots. |
| **Review/inspection** | `ce status`, `ce checklist`, `ce doctor [--ai-profile corporate]`, `ce ai-governance status` | Read-only dashboards plus AI profile enforcement, ROI snapshots and Git hook diagnostics for governance ceremonies, stand-ups or leadership reviews. |
| **Guided / automation** | `ce wizard`, `ce autopilot`, `ce ci-bootstrap` | Wizard confirms each phase, Autopilot runs unattended (can resume from PRD/PRPs/Tasks), CI bootstrap wires GitHub Actions calling `ce validate` + `ce report`. |

> All tracks honor `--ai/--no-ai` and the embedding settings resolved by the AI Governance service.

### 2.1 Release checklist (PyPI + GitHub Actions)
1. Run validations: `pytest -q && ruff check .` (plus stack-specific linters).
2. Diagnose AI stack: `ce doctor --format table [--ai-profile corporate]` and `ce ai-governance status --format table` to confirm ROI metrics and Git hook status.
3. Sync prompts/workflows: `ce ide sync --project-dir .` (commit `.IDE/` if multiple IDEs share the repo).
4. Refresh CI workflow: `ce ci-bootstrap --project-dir .` whenever governance rules or policies change.
5. Build & publish: `python -m build && twine upload dist/*`.
6. Tag & push: `git tag vX.Y.Z && git push --tags`.

### 3. Working with AI-enabled IDEs

Regardless of the IDE, follow these constants:

1. Keep the `.IDE/prompts/` and `.IDE/workflows/` folders synchronized with `ce ide sync --project-dir .` (fallback: copy `IDE` → `.IDE/`) before referencing prompts via `@`.
2. Reference prompts directly in IDE (`@Agente_PRD_360.md`) or copy/paste the full file in IDEs that do not understand `@`.
3. Always mention the global rules and stack standards before asking copilots to execute PRD/PRP/Task flows.
4. Use the functional map (Mermaid/PNG) to explain how the CLI and conversational flows stay aligned.

#### 3.1 VS Code + Copilot / IDE AI

```bash
# Open the prompt file
code .IDE/prompts/Agente_PRD_360.md
```

- Copy the full contents into the Copilot chat.
- Add the project-specific idea/context at the end of the prompt.
- When referencing additional files (e.g., `GLOBAL_ENGINEERING_RULES.json` or `PROJECT_STANDARDS.md`), paste their contents beneath the main prompt.

#### 3.2 JetBrains AI Assistant

- Use `cat .IDE/prompts/Agente_PRD_360.md` or open the file in the built-in terminal.
- Press `Ctrl+Shift+A` (Windows/Linux) or `Cmd+Shift+A` (macOS) and search for “AI Assistant”.
- Paste the content of the prompt plus your input. Repeat for follow-up files (PRD, PRPs, tasks).

#### 3.3 Windsurf, Antigravity

- **Windsurf**: leverage `/load .[your.IDE]/prompts/Agente_PRD_360.md`.
- **Antigravity**: paste the full prompt and mention additional files explicitly.

#### 3.4 Universal Strategy

1. Copy the entire prompt content.
2. Mention the global rules (`GLOBAL_ENGINEERING_RULES.json`) and stack definition (`PROJECT_STANDARDS.md`).
3. Provide the concrete idea/User Story at the end.
4. Reuse the same approach for PRPs (`Agente_PRP_Orquestrador.md`) and Task execution (`@TASKs/TASK.FR-001.md` or `@Agente_Task_Direto.md`).

### 4. CLI-only workflow (no AI)

Even without AI integrations, the Python CLI covers validation, estimation, governance and dashboards.

#### 4.1 Installation

```bash
pip install -e .
# or, with uv (faster):
uv pip install -e .
ce --help
```

#### 4.2 Validation & governance

```bash
ce validate ./PRPs \
  --prd-file ./prd/prd_structured.json \
  --tasks-dir ./TASKs

ce validate ./PRPs --soft-check        # consultative mode for Git hooks
ce install-hooks                       # Soft-Gate
ce install-hooks --hard-gate           # Hard-Gate
```

#### 4.3 Effort estimation

```bash
ce estimate-effort TASKs/TASK.FR-001.json \
  --stack python-fastapi \
  --project-name meu-projeto

ce estimate-batch TASKs/ \
  --stack python-fastapi \
  --project-name meu-projeto \
  --output estimates.json
```

#### 4.4 Dashboards & metrics

```bash
ce report --project-name meu-projeto            # HTML/text dashboard
ce report --project-name meu-projeto --format json > metrics.json
ce metrics-summary --project-name meu-projeto --tasks-dir ./TASKs
```

#### 4.5 Mock server & contracts

```bash
ce mock-server ./PRPs/openapi.yaml --port 4010
# Requires @stoplight/prism-cli (install via npm)
```

#### 4.6 Context pruning API

```python
from core.engine import ContextEngine
from pathlib import Path

engine = ContextEngine()
files = [Path("PRD.md"), Path("logs/app.log")]

compressed = engine.compress_context(
    files=files,
    max_tokens=100000,
    preserve_core=True,
    project_name="meu-projeto",
)
```

### 5. Programmatic integration

```python
#!/usr/bin/env python3
"""
Script using Context Engineer without AI copilots.
"""
import sys
from pathlib import Path

sys.path.insert(0, "./libs/context-engineer")

from core.validators import PRPValidator
from core.planning import EffortEstimator
from core.metrics import MetricsCollector

validator = PRPValidator(Path("./libs/context-engineer/schemas"))
results = validator.validate_all(
    prps_dir=Path("./PRPs"),
    prd_file=Path("./prd/prd_structured.json"),
    tasks_dir=Path("./TASKs"),
)
metrics = MetricsCollector(Path("./.cache/metrics"))
estimator = EffortEstimator(metrics)
points = estimator.estimate_effort_points(
    task={"artifacts": [...], "steps": [...]},
    stack="python-fastapi",
    project_name="meu-projeto",
)
```

### 6. Representative scenarios (English)

1. **VS Code + Copilot**: Copy prompts, use CLI for validation, install Git hooks for governance, leverage the PNG diagram to brief the team.
2. **IDE without AI (Vim, Emacs, etc.)**: Follow templates manually, then run `ce validate`, `ce estimate-batch`, `ce report`, and rely on hooks for enforcement.
3. **CI/CD pipeline**: Invoke the CLI in GitHub Actions (or any runner) to validate PRPs, generate metrics artifacts and block merge when required.

### 7. IDE adaptation matrix

| IDE / Environment | Adaptation |
|-------------------|------------|
| IDE | Native `@file` references. |
| VS Code + Copilot | Copy/paste prompts, mention rules and stack in the same chat. |
| JetBrains AI | Use AI Assistant panels, copy prompts sequentially. |
| Windsurf | `/load` command + optional direct file references. |
| Lovable / Bolt | Paste prompts, mention additional files inline. |
| CLI only | Follow templates manually, rely on validation hooks and dashboards. |

### 8. Compatibility checklist & next steps

- [ ] Prompts copied or referenced.
- [ ] `.IDE/prompts/` synchronized.
- [ ] Global rules + stack defined.
- [ ] CLI installed and usable.
- [ ] Hooks installed (optional).
- [ ] Diagram (Mermaid/PNG) shared with the team.

Next steps:
1. Pick the interaction track that matches your ceremony (conversational, review, automation).
2. Share the PNG diagram as onboarding material.
3. Keep prompts updated as the repository evolves.

-### 9. Related documentation (English)
-
- `docs/MAIN_USAGE_GUIDE.md` – full walkthrough (IDE focus).
- `docs/QUICK_REFERENCE.md` – commands recap.
- `docs/AI_GOVERNANCE.md` – how Soft-Gate governance aligns with terminal modes.
- `docs/examples/ai_governance_policy.py` – extending policies.

### 10. Diagram reference

- Mermaid source: `docs/assets/context_engineer_flow.mmd`
- PNG fallback: `docs/assets/context_engineer_flow.png`
- Render manually (optional): `npx @mermaid-js/mermaid-cli -i docs/assets/context_engineer_flow.mmd -o docs/assets/context_engineer_flow.png`

---

## Referência em Português

> A seção em inglês acima é a referência principal. Abaixo está a versão detalhada em português cobrindo os mesmos tópicos e mencionando o diagrama (`docs/assets/context_engineer_flow.mmd` / `docs/assets/context_engineer_flow.png`).

## Visão Geral

O Context Engineer foi projetado para ser **agnóstico à IDE** e funcionar **com ou sem IA**:

- **Com IA**: Funciona em qualquer IDE com assistente de IA (IDE, VS Code+Copilot, JetBrains AI, Windsurf, etc.)
- **Sem IA**: Todas as validações, estimativas, métricas e governança funcionam via CLI Python

> O mapeamento funcional completo dos fluxos (Ideia → PRD → PRPs → Tasks → Governança) está em `docs/assets/context_engineer_flow.mmd`. Caso não tenha suporte ao Mermaid, utilize `docs/assets/context_engineer_flow.png`.

### Trilhas de uso no terminal (Português)

| Trilha | Comando(s) | Quando usar |
|--------|------------|-------------|
| **Assistente conversacional** | `ce assist --format text`, `ce assist --format html --open` | Mistura inspeção do projeto, sugestões de padrões/cache e execução inline (`ce init`, `ce generate-*`). Ideal para pareamento com copilotos. |
| **Revisão/inspeção** | `ce status`, `ce checklist` | Dashboards somente leitura para rituais de governança, dailies ou reviews executivos. |
| **Guiado / automação** | `ce wizard`, `ce autopilot`, `ce ci-bootstrap` | Wizard confirma cada fase, Autopilot roda sem intervenção (pode retomar de PRD/PRPs/Tasks), CI bootstrap integra `ce validate` + `ce report` nos pipelines. |

Todos os modos respeitam `--ai/--no-ai` e as preferências calculadas pelo AI Governance Service.

### Como acessar o diagrama

- **Fonte Mermaid**: `docs/assets/context_engineer_flow.mmd`
- **PNG pronto**: `docs/assets/context_engineer_flow.png`
- **Renderização opcional**: `npx @mermaid-js/mermaid-cli -i docs/assets/context_engineer_flow.mmd -o docs/assets/context_engineer_flow.png`

---

## Uso em Outras IDEs com IA

### VS Code + GitHub Copilot / IDE AI

**Diferença**: VS Code não suporta a sintaxe `@arquivo.md` do IDE.

**Solução**: Copiar e colar o conteúdo dos prompts.

#### Passo a Passo:

1. **Copiar o prompt**:
 ```bash
 # Abra o arquivo do prompt
 code .IDE/prompts/Agente_PRD_360.md
 
 # Copie TODO o conteúdo
 ```

2. **Usar no Copilot/IDE AI**:
 ```
 [Cole o conteúdo completo do prompt aqui]
 
 Faça o processo descrito para a ideia: [sua ideia aqui]
 ```

3. **Para referenciar outros arquivos**:
 ```
 [Conteúdo do prompt]
 
 Use as regras globais de: [cole conteúdo de GLOBAL_ENGINEERING_RULES.json]
 Use a stack definida em: [cole conteúdo de PROJECT_STANDARDS.md]
 ```

#### Exemplo Completo:

```
# Cole aqui o conteúdo de Agente_PRD_360.md

---

Faça o processo descrito para a ideia:

"Um sistema de gestão de tarefas para equipes remotas com integração Slack"
```

---

### JetBrains IDEs (IntelliJ, PyCharm, WebStorm) + AI Assistant

**Funciona igual ao VS Code**: Copiar e colar prompts.

#### Passo a Passo:

1. **Abrir prompt**:
 ```bash
 # No terminal do JetBrains
 cat .IDE/prompts/Agente_PRD_360.md
 ```

2. **Usar AI Assistant**:
 - Pressione `Ctrl+Shift+A` (Windows/Linux) ou `Cmd+Shift+A` (Mac)
 - Digite "AI Assistant"
 - Cole o prompt completo + sua entrada

3. **Para múltiplos arquivos**:
 - Abra cada arquivo em abas separadas
 - Cole o conteúdo sequencialmente no chat

---

### Windsurf, Lovable, Bolt

**Já compatíveis!** Os prompts mencionam explicitamente essas ferramentas.

#### Adaptação:

- **Windsurf**: Use `/` para referenciar arquivos ou copie conteúdo
- **Lovable**: Cole prompts diretamente
- **Bolt**: Similar ao IDE, mas pode precisar ajustar sintaxe `@`

#### Exemplo Windsurf:

```
/load .IDE/prompts/Agente_PRD_360.md

Faça o processo descrito para: [sua ideia]
```

---

### Outras IDEs com IA

**Estratégia Universal**:

1. Copie o conteúdo completo dos prompts
2. Mantenha a estrutura `.IDE/prompts/` (ou adapte conforme necessário)
3. Cole no chat da IA da sua IDE
4. Adicione sua entrada específica no final

**Arquivos essenciais**:
- `.IDE/prompts/Agente_PRD_360.md` - Geração de PRD
- `.IDE/prompts/Agente_PRP_Orquestrador.md` - Geração de PRPs
- `.IDE/prompts/Agente_Task_Direto.md` - Execução direta de Tasks
- `.IDE/prompts/GLOBAL_ENGINEERING_RULES.json` - Regras globais
- `.IDE/prompts/PROJECT_STANDARDS.md` - Padrões do projeto

---

## Uso Sem IA (Apenas CLI e Validacoes)

**Todas as funcionalidades funcionam sem IA!** O CLI Python fornece validação, estimativa, métricas e governança baseadas em regras.

### Instalação

```bash
# Instalar Context Engineer CLI
pip install -e .
# ou com uv
uv pip install -e .

# Verificar instalação
ce --help
```

---

### 1. Validação de PRPs e Tasks

**Funciona 100% sem IA** - Baseado em regras e schemas JSON.

```bash
# Validação completa de rastreabilidade
ce validate ./PRPs \
 --prd-file ./prd/prd_structured.json \
 --tasks-dir ./TASKs

# Validação de contratos (Deep Cross-Validation)
ce validate ./PRPs \
 --api-spec ./PRPs/openapi.yaml \
 --ui-tasks-dir ./TASKs

# Validação consultiva (para Git hooks)
ce validate ./PRPs --soft-check
```

**O que valida**:
- Rastreabilidade PRD → PRPs → Tasks
- Consistência de dependências
- Integridade de contratos API ↔ UI
- Schemas JSON válidos
- Estrutura de arquivos correta

---

### 2. Estimativa de Esforço

**Funciona 100% sem IA** - Baseado em algoritmos de complexidade.

```bash
# Estimar uma task específica
ce estimate-effort TASKs/TASK.FR-001.json \
 --stack python-fastapi \
 --project-name meu-projeto

# Estimar todas as tasks
ce estimate-batch TASKs/ \
 --stack python-fastapi \
 --project-name meu-projeto \
 --output estimates.json

# Com breakdown detalhado
ce estimate-effort TASKs/TASK.FR-001.json \
 --stack python-fastapi \
 --detailed
```

**Como funciona**:
- Analisa complexidade (artefatos, passos, testes, dependências)
- Aplica fatores de stack (python-fastapi: 0.3, go-gin: 0.3, etc.)
- Ajusta por categoria (security: +0.6, etc.)
- Usa histórico de rework (Confidence Adjustment)
- Retorna Story Points (Fibonacci: 1, 2, 3, 5, 8, 13)

---

### 3. Dashboard de Métricas

**Funciona 100% sem IA** - Coleta e analisa métricas automaticamente.

```bash
# Relatório completo de um projeto
ce report --project-name meu-projeto

# Relatório em JSON (para integração)
ce report --project-name meu-projeto --format json

# Relatório agregado (todos os projetos)
ce report

# Filtrar por stack
ce report --stack python-fastapi
```

**Métricas coletadas**:
- Taxa de conclusão de tasks
- Taxa de retrabalho (rework rate)
- Cobertura de testes
- Qualidade do código
- Tempo de geração de PRP
- ROI de Context Pruning (tokens economizados)
- Análise de risco (alto/médio/baixo)

---

### 4. Git Hooks (Governança)

**Funciona 100% sem IA** - Validação automática antes de push.

```bash
# Instalar hooks consultivos (Soft-Gate)
ce install-hooks

# Instalar hooks bloqueantes (Hard-Gate)
ce install-hooks --hard-gate

# Em projeto específico
ce install-hooks --project-dir ./meu-projeto
```

**O que faz**:
- Valida PRPs antes de cada push
- Valida contratos (API ↔ UI)
- Mostra métricas de contexto quantitativo
- Solicita confirmação (Soft-Gate) ou bloqueia (Hard-Gate)
- Previne código sem rastreabilidade no repositório

---

### 5. Mock Server

**Funciona 100% sem IA** - Gera servidor mock a partir de OpenAPI.

```bash
# Iniciar mock server
ce mock-server ./PRPs/openapi.yaml --port 4010

# Requer Prism instalado:
npm install -g @stoplight/prism-cli
```

**Uso**:
- Desenvolvimento de UI sem backend
- Testes de integração
- Validação de contratos em tempo real

---

### 6. Context Pruning

**Funciona 100% sem IA** - Compressão inteligente de contexto.

```python
from core.engine import ContextEngine
from pathlib import Path

engine = ContextEngine()
files = [Path("PRD.md"), Path("logs/app.log")]

compressed = engine.compress_context(
 files=files,
 max_tokens=100000,
 preserve_core=True,
 project_name="meu-projeto"
)
```

**Estratégias**:
- Logs: Mantém últimas 100 linhas
- Métricas JSON: Resume em estatísticas
- Markdown: Extrai headers e seções-chave
- Preserva arquivos core (PRD, Tasks atuais)

---

## Comparação: Com IA vs Sem IA

| Funcionalidade | Com IA | Sem IA (CLI) |
|----------------|--------|--------------|
| **Geração de PRD** | Via prompts | Manual |
| **Geração de PRPs** | Via prompts | Manual |
| **Geração de Tasks** | Via prompts | Manual |
| **Validação** | Via prompts | **CLI completo** |
| **Estimativa** | Via prompts | **CLI completo** |
| **Métricas** | Via prompts | **CLI completo** |
| **Git Hooks** | Via prompts | **CLI completo** |
| **Mock Server** | Via prompts | **CLI completo** |
| **Context Pruning** | Via prompts | **Programático** |

---

## Uso Programático (Sem IA)

Para integração em scripts ou ferramentas:

```python
#!/usr/bin/env python3
"""
Script usando Context Engineer sem IA
"""
import sys
from pathlib import Path

sys.path.insert(0, "./libs/context-engineer")

from core.validators import PRPValidator
from core.planning import EffortEstimator
from core.metrics import MetricsCollector
from core.engine import ContextEngine

# Validação
validator = PRPValidator(Path("./libs/context-engineer/schemas"))
results = validator.validate_all(
 prps_dir=Path("./PRPs"),
 prd_file=Path("./prd/prd_structured.json"),
 tasks_dir=Path("./TASKs")
)

# Estimativa
metrics = MetricsCollector(Path("./.cache/metrics"))
estimator = EffortEstimator(metrics)
points = estimator.estimate_effort_points(
 task={"artifacts": [...], "steps": [...]},
 stack="python-fastapi",
 project_name="meu-projeto"
)

# Métricas
roi = metrics.get_roi_metrics("meu-projeto")
print(f"Tokens economizados: {roi['tokens_saved']}")
```

---

## Casos de Uso

### Caso 1: Equipe usando VS Code + Copilot

**Estratégia**:
1. Instalar CLI: `pip install -e .`
2. Copiar prompts para usar no Copilot
3. Usar CLI para validação e métricas
4. Git hooks automáticos

**Fluxo**:
```bash
# 1. Gerar PRD (copiar prompt no Copilot)
# 2. Gerar PRPs (copiar prompt no Copilot)
# 3. Validar automaticamente
ce validate ./PRPs --tasks-dir ./TASKs

# 4. Estimar esforço
ce estimate-batch ./TASKs --stack python-fastapi

# 5. Ver métricas
ce report --project-name meu-projeto
```

---

### Caso 2: IDE sem IA (Vim, Emacs, etc.)

**Estratégia**:
1. Usar apenas CLI para validação
2. Criar PRDs/PRPs manualmente seguindo templates
3. Validar com CLI antes de commit
4. Usar Git hooks para validação automática

**Fluxo**:
```bash
# 1. Criar PRD manualmente (seguindo template)
# 2. Criar PRPs manualmente (seguindo template)
# 3. Validar
ce validate ./PRPs

# 4. Git hooks validam automaticamente
git push # Hooks executam ce validate automaticamente
```

---

### Caso 3: CI/CD Pipeline

**Estratégia**:
1. Usar CLI em pipeline
2. Validar PRPs antes de merge
3. Gerar relatórios de métricas
4. Bloquear merge se validação falhar

**Exemplo GitHub Actions**:
```yaml
name: Context Engineer Validation

on: [pull_request]

jobs:
 validate:
 runs-on: ubuntu-latest
 steps:
 - uses: actions/checkout@v3
 - uses: actions/setup-python@v4
 with:
 python-version: '3.11'
 - run: pip install -e ./libs/context-engineer
 - run: ce validate ./PRPs --tasks-dir ./TASKs
 - run: ce report --project-name ${{ github.repository }} --format json > metrics.json
 - uses: actions/upload-artifact@v3
 with:
 name: metrics
 path: metrics.json
```

---

## Adaptações por IDE

### IDE (Nativo)
```markdown
@Agente_PRD_360.md
Faça o processo descrito para: [ideia]
```

### VS Code + Copilot
```markdown
[Cole conteúdo completo de Agente_PRD_360.md]

Faça o processo descrito para: [ideia]
```

### JetBrains AI
```markdown
[Cole conteúdo completo de Agente_PRD_360.md]

Faça o processo descrito para: [ideia]
```

### Windsurf
```markdown
/load .IDE/prompts/Agente_PRD_360.md

Faça o processo descrito para: [ideia]
```

### Sem IA (CLI)
```bash
# Criar PRD manualmente seguindo template
# Validar estrutura
ce validate ./PRPs
```

---

## Checklist de Compatibilidade

### Para IDEs com IA:
- [ ] Prompts copiados e adaptados
- [ ] Estrutura `.IDE/prompts/` mantida
- [ ] Regras globais configuradas
- [ ] Stack definida em `PROJECT_STANDARDS.md`

### Para Uso Sem IA:
- [ ] CLI instalado (`pip install -e .`)
- [ ] Comando `ce` disponível
- [ ] Git hooks instalados (opcional)
- [ ] Templates seguidos para criação manual

---

## Próximos Passos

1. **Com IA**: Escolha sua IDE e adapte os prompts conforme este guia
2. **Sem IA**: Instale o CLI e use validações/métricas automaticamente
3. **Híbrido**: Use IA para geração e CLI para validação

---

## Documentação Relacionada

- **[MAIN_USAGE_GUIDE.md](MAIN_USAGE_GUIDE.md)** - Guia completo (focado em IDE)
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Referência rápida de comandos CLI
- **[docs/AI_GOVERNANCE.md](docs/AI_GOVERNANCE.md)** - Sistema de Governança
- **[docs/NEW_STACK_ONBOARDING_GUIDE.md](docs/NEW_STACK_ONBOARDING_GUIDE.md)** - Adicionar novas stacks

---

## Dicas

1. **Mantenha prompts atualizados**: Os prompts evoluem, mantenha versões sincronizadas
2. **Use CLI para validação**: Mesmo com IA, valide com CLI antes de commit
3. **Git hooks são universais**: Funcionam em qualquer IDE/Git
4. **Métricas funcionam sempre**: Coletam dados mesmo sem IA

---

**Status**: **Compatível com qualquer IDE e funciona sem IA**

**Conclusão**: O Context Engineer é **agnóstico à IDE** e **funciona completamente sem IA** para validações, estimativas, métricas e governança!
