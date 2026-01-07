# Context Engineer - Referência Rápida

> **Language Navigation / Navegação**
> - [English Reference](#english-reference)
> - [Referência em Português](#referencia-em-portugues)
>
> **Language note:** `@Agente_PRD_360.md` now prompts for EN-US or PT-BR before generating the PRD/JSON. Keep bilingual inputs handy so the agent can mirror the preferred language.

## English Reference

### Essential Commands
| Track | Command(s) | Outcome |
|-------|------------|---------|
| Conversational assistant | `ce assist --format text`, `ce assist --format html --open` | Reads project metrics, suggests patterns/cache entries and can trigger `ce init`, `ce generate-prd`, `ce generate-prps`, `ce generate-tasks`. |
| Review / inspection | `ce status`, `ce checklist`, `ce doctor [--ai-profile corporate]`, `ce ai-governance status` | Read-only dashboards plus AI profile enforcement, ROI snapshots and Git hook diagnostics for governance checkpoints and daily stand-ups. |
| Guided execution | `ce wizard` | Asks confirmation before each phase, ideal for workshops. |
| Hands-off automation | `ce autopilot [--idea-file|--prd-file|--prps-dir|--tasks-dir]`, `ce ci-bootstrap` | Runs the entire pipeline unattended or wires GitHub Actions with the same validation hooks. |

> All tracks honor `--ai / --no-ai` and the embedding configuration enforced by the AI Governance service.

### Flow Cheatsheet
0. **Prompt sync**: run `ce ide sync --project-dir .` (fallback: copy `IDE-rules` → `.{name of your ide)/`) so `@` references resolve to the latest prompts/workflows.
1. **Setup**: configure `GLOBAL_ENGINEERING_RULES.json` and `PROJECT_STANDARDS.md`.
2. **PRD generation**: `@Agente_PRD_360.md` → outputs `PRD.md` + `prd_structured.json`.
3. **PRPs**: `@Agente_PRP_Orquestrador.md` referencing the structured PRD → outputs `PRPs/`, `TASKs/`, `execution_map.md`.
4. **Tasks**: `@TASKs/TASK.FR-001.md` or `ce generate-tasks`.
5. **Patterns & marketplace**: `ce patterns list/show/suggest`, `ce marketplace install`.
6. **Traceability validation**: `ce validate prps/ --prd-file ... --tasks-dir ... --commits-json ...`.

### Assets
- Diagram (Mermaid + PNG): `docs/assets/context_engineer_flow.mmd` / `context_engineer_flow.png`.
- File structure overview and PRP phase table retained below (Portuguese section) with the same commands mirrored.

### Release checklist (PyPI + GitHub Actions)
1. Run validations: `pytest -q && ruff check .` (plus stack-specific linters).
2. Diagnose AI stack: `ce doctor --format table [--ai-profile corporate]` and `ce ai-governance status --format table` to confirm ROI + Git hook health.
3. Sync prompts/workflows: `ce ide sync --project-dir .` (commit `.ide-rules/` if shared).
4. Refresh CI workflow: `ce ci-bootstrap --project-dir .` whenever governance policies change.
5. Build & publish: `python -m build && twine upload dist/*`.
6. Tag & push: `git tag vX.Y.Z && git push --tags`.

---

## Referência em Português

### Comandos Essenciais

### Interaction Tracks

| Mode | Commands | Outcome |
|------|----------|---------|
| **Assistente conversacional** | `ce assist --format text`, `ce assist --format html --open` | Fluxo guiado que lê métricas do projeto, sugere padrões/cache e pode acionar `init`, `generate-prd`, `generate-prps`, `generate-tasks`. |
| **Revisão/inspeção** | `ce status`, `ce checklist`, `ce doctor [--ai-profile corporativo]`, `ce ai-governance status` | Dashboards somente leitura com enforcement de perfis de IA, ROI e status dos hooks para rituais de governança e dailies. |
| **Execução guiada** | `ce wizard` | Pede confirmação em cada fase, ideal para workshops. |
| **Automação completa** | `ce autopilot [--idea-file|--prd-file|--prps-dir|--tasks-dir]`, `ce ci-bootstrap` | Roda o pipeline inteiro sem intervenção ou configura GitHub Actions com os mesmos validadores. |

> Todos os modos respeitam `--ai / --no-ai` e o modelo configurado pelo serviço de governança.

### Setup Inicial (Passo 0)
```bash
# 0. Sincronizar prompts/workflows oficiais
ce ide sync --project-dir .

# 1. Configurar regras globais
code .ide-rules/prompts/GLOBAL_ENGINEERING_RULES.json

# 2. Definir stack tecnológica 
code .ide-rules/prompts/PROJECT_STANDARDS.md

# 3. Configurar agentes
code .ide-rules/prompts/AGENTS.md
```

### Checklist de Release (PyPI + GitHub Actions)
1. Execute validações: `pytest -q && ruff check .` (e linters específicos da stack).
2. Rode diagnósticos: `ce doctor --format table [--ai-profile corporativo]` e `ce ai-governance status --format table` para garantir ROI e status dos hooks.
3. Sincronize prompts/workflows: `ce ide sync --project-dir .` (versione `.ide-rules/` se for compartilhado).
4. Atualize o workflow de CI: `ce ci-bootstrap --project-dir .` sempre que políticas mudarem.
5. Gere e publique pacotes: `python -m build && twine upload dist/*`.
6. Versione: `git tag vX.Y.Z && git push --tags`.

### Geração de PRD (Passo 1)
```
# Na sua IDE, use:
@Agente_PRD_360.md
Faça o processo descrito para a ideia: [sua ideia]

# Output: PRD.md + prd_structured.json
```

### Geração de PRPs (Passo 2)
```
# No IDE, use:
@Agente_PRP_Orquestrador.md
Faça o processo descrito usando: @prd_structured.json

# Output: PRPs/ + TASKs/ + execution_map.md
```

### Execução de Tarefas (Passo 3)
```
# No IDE, use:
@TASKs/TASK.FR-001.md
Execute a task descrita acima seguindo todos os passos.
```

### Biblioteca de Padrões
```bash
# Listar padrões com filtros
ce patterns list --stack python-fastapi --category authentication

# Mostrar detalhes completos
ce patterns show AUTH.JWT

# Sugerir padrões conforme PRD/stack do projeto atual
ce patterns suggest --project-dir .

# Instalar aceleradores do marketplace local
ce marketplace list
ce marketplace install pattern_api_gateway --project-dir .
```

### Rastreabilidade Inversa (Tasks → Commits/PRs)
```bash
# Validar PRPs + rastreabilidade completa incluindo commits
ce validate prps/ --prd-file prd/prd_structured.json \
  --tasks-dir TASKs/ --commits-json docs/examples/commit-mapping.example.json \
  --project-name minha-api

# Deploy rápido
docker build -t app . && docker run -p 8000:8000 app
```

---

## Estrutura de Arquivos

```
Context Engineer/
├── prompts/ # Prompts dos agentes
│ ├── Agente_PRD_360.md # Geração de PRD
│ ├── Agente_PRP_Orquestrador.md # Orquestração de PRPs
│ ├── GLOBAL_ENGINEERING_RULES.json # Regras globais
│ ├── PROJECT_STANDARDS.md # Stack tecnológica
│ └── AGENTS.md # Configurações de agentes
├── workflows/ # Templates por fase
├── PRPs/ # Planos de implementação (gerado)
├── TASKs/ # Tarefas individuais (gerado)
├── docs/ # Documentação
└── execution_map.md # Ordem de execução (gerado)
```

---

## Fases dos PRPs

| Fase | Arquivo | Objetivo | Validação |
|------|---------|----------|-----------|
| **F0** | `00_plan.md/.json` | Backlog e planejamento | Épicos priorizados |
| **F1** | `01_scaffold.md/.json` | Arquitetura e estrutura | Clean Architecture |
| **F2** | `02_data_model.md/.json` | Modelo de dados | Constraints válidas |
| **F3** | `03_api_contracts.md/.json` | Contratos de API | OpenAPI válido |
| **F4** | `04_ux_flows.md/.json` | Fluxos de UX | Happy + edge cases |
| **F5** | `TASKs/TASK.*.md/.json` | Implementação guiada | Testes passando |
| **F6** | `05_quality.md/.json` | Testes e qualidade | Cobertura ≥ 80% |
| **F7** | `06_observability.md/.json` | Monitoramento | Eventos rastreáveis |
| **F8** | `07_security.md/.json` | Segurança e compliance | 0 vulnerabilidades |
| **F9** | `08_ci_cd_rollout.md/.json` | CI/CD e deploy | Pipeline funcionando |

---

## Functional Flow Reference

Render the complete Context Engineer functional map (`docs/assets/context_engineer_flow.mmd`) with any Mermaid viewer to visualize how ideas evolve into validated code and how conversational/review/automation tracks interact with governance services.

---

## Comandos de Validação

### Python/FastAPI
```bash
# Linting e formatação
ruff check . && black --check .

# Testes
pytest -v --cov=src --cov-report=term-missing

# Segurança
bandit -r src/ && safety check

# Tipo checking
mypy src/
```

### Node.js/React
```bash
# Linting e formatação
npm run lint && npm run format:check

# Testes
npm run test:coverage

# Tipo checking
npm run type-check

# Build
npm run build
```

### Vue 3
```bash
# Linting e formatação
npm run lint && npm run format

# Testes
npm run test:unit

# Tipo checking
npm run type-check

# Build
npm run build
```

### Contratos de API
```bash
# Validar OpenAPI
openapi-spec-validator openapi.yaml

# Testes de contrato
pytest tests/contracts/ -v
```

---

## Regras Críticas

### Sempre Fazer
- [ ] Busca semântica no codebase antes de gerar código
- [ ] Validação automática após cada mudança
- [ ] Clean Architecture (domain/app/infra/interfaces)
- [ ] Testes unitários + integração + contrato
- [ ] Logs estruturados em JSON
- [ ] LGPD compliance por design
- [ ] Performance budgets respeitados
- [ ] Documentação em inglês, explicações em PT-BR

### Nunca Fazer
- [ ] Código sem testes
- [ ] PII em logs
- [ ] Secrets em código
- [ ] Deploy sem rollback
- [ ] APIs sem versionamento
- [ ] Decisões arquiteturais não documentadas
- [ ] Validações manuais
- [ ] Código duplicado (DRY)

---

## Performance Budgets

| Métrica | Limite | Validação |
|---------|--------|-----------|
| **API p95** | ≤ 200ms | `curl -w "@curl-format.txt"` |
| **Frontend Bundle** | ≤ 250KB | `npm run build --analyze` |
| **Cobertura de Testes** | ≥ 80% | `pytest --cov-report=term` |
| **Vulnerabilidades** | 0 críticas | `bandit -r src/` |
| **Linting Errors** | 0 | `ruff check .` |

---

## Templates de Código

### Entidade (Domain)
```python
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class Entity(SQLModel, table=True):
 id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
 created_at: datetime = Field(default_factory=datetime.utcnow)
 updated_at: datetime = Field(default_factory=datetime.utcnow)
 is_active: bool = Field(default=True)
```

### Serviço (Application)
```python
from abc import ABC, abstractmethod

class ServiceInterface(ABC):
 @abstractmethod
 async def execute(self, input_data: InputDTO) -> OutputDTO:
 pass

class Service(ServiceInterface):
 def __init__(self, repository: RepositoryInterface):
 self.repository = repository
 
 async def execute(self, input_data: InputDTO) -> OutputDTO:
 # Business logic here
 pass
```

### Controller (Interface)
```python
from fastapi import APIRouter, Depends, HTTPException
from src.application.services.service import Service

router = APIRouter(prefix="/api/v1", tags=["resource"])

@router.post("/resource", response_model=OutputDTO)
async def create_resource(
 input_data: InputDTO,
 service: Service = Depends()
) -> OutputDTO:
 try:
 return await service.execute(input_data)
 except BusinessException as e:
 raise HTTPException(status_code=400, detail=str(e))
```

### Componente React
```typescript
interface ComponentProps {
 data: DataType;
 onAction: (id: string) => void;
 loading?: boolean;
 'aria-label': string; // Acessibilidade obrigatória
}

export const Component: React.FC<ComponentProps> = ({
 data,
 onAction,
 loading = false,
 'aria-label': ariaLabel
}) => {
 return (
 <div className="component-container" aria-label={ariaLabel}>
 {loading ? <Spinner /> : <Content data={data} onAction={onAction} />}
 </div>
 );
};
```

---

## Troubleshooting

### Problema: Agente não segue regras
**Solução:**
```bash
# Verificar se arquivos de configuração estão carregados
ls -la prompts/
cat prompts/GLOBAL_ENGINEERING_RULES.json | jq .
```

### Problema: Validações falhando
**Solução:**
```bash
# Executar comandos manualmente para debug
pytest tests/ -v -s
ruff check . --show-source
```

### Problema: Performance ruim
**Solução:**
```bash
# Profiling de API
curl -w "@curl-format.txt" http://localhost:8000/api/endpoint

# Análise de bundle
npm run build --analyze
```

### Problema: Testes não passam
**Solução:**
```bash
# Executar testes com mais detalhes
pytest -v -s --tb=long

# Verificar cobertura
pytest --cov=src --cov-report=html
```

---

## Links Úteis

### Documentação
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [LGPD Guide](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)

### Ferramentas
- [Ruff](https://docs.astral.sh/ruff/) - Python linting
- [Black](https://black.readthedocs.io/) - Python formatting
- [PyTest](https://docs.pytest.org/) - Python testing
- [Vite](https://vitejs.dev/) - Frontend tooling
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework

### Monitoramento
- [OpenTelemetry](https://opentelemetry.io/) - Observability
- [DataDog](https://www.datadoghq.com/) - APM
- [Sentry](https://sentry.io/) - Error tracking

---

## Checklist de Projeto

### Setup (Passo 0)
- [ ] `GLOBAL_ENGINEERING_RULES.json` configurado
- [ ] `PROJECT_STANDARDS.md` definido
- [ ] `AGENTS.md` ajustado
- [ ] Stack tecnológica escolhida

### PRD (Passo 1)
- [ ] Ideia de produto clara
- [ ] Contexto de negócio definido
- [ ] Usuários e personas identificados
- [ ] Restrições e constraints listadas
- [ ] `PRD.md` gerado e revisado
- [ ] `prd_structured.json` válido

### PRPs (Passo 2)
- [ ] Todos os PRPs gerados (F0-F9)
- [ ] TASKs criadas para cada FR-*
- [ ] `execution_map.md` disponível
- [ ] `openapi.yaml` especificado
- [ ] Dependências mapeadas

### Implementação (Passo 3)
- [ ] Todas as TASKs executadas
- [ ] Testes passando (≥ 80% cobertura)
- [ ] Linting sem erros
- [ ] Performance budgets respeitados
- [ ] Segurança validada
- [ ] LGPD compliance verificado

### Deploy (Passo 4)
- [ ] CI/CD configurado
- [ ] Ambientes criados (dev/staging/prod)
- [ ] Monitoramento ativo
- [ ] Rollback testado
- [ ] Documentação atualizada

---

## Comandos de Início Rápido

```bash
# Setup completo em 3 comandos
code prompts/GLOBAL_ENGINEERING_RULES.json # Configure regras
code prompts/PROJECT_STANDARDS.md # Defina stack
```

```
# No IDE, execute PRD:
@Agente_PRD_360.md
Faça o processo descrito para a ideia: [sua ideia]
```

# Validação rápida
pytest -q && ruff check . && black --check .

# Deploy rápido
docker build -t app . && docker run -p 8000:8000 app
```

**Pronto para começar!**

```

---

## Fluxos Automatizados

```bash
# Pipeline completo gerenciado pelo Autopilot
ce autopilot --idea-file docs/exemplos/minha_ideia.md --project-dir ./workspace

# Gerar workflow padrão de CI com validação consultiva
ce ci-bootstrap --project-dir ./workspace

# Diagnosticar modo IA e embeddings configurados
ce ai-status --project-dir ./workspace
```
