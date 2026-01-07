# Context Engineer Marketplace

> **Language Navigation / Navegação**
> - [English Reference](#english-reference)
> - [Referência em Português](#referencia-em-portugues)

---

## English Reference

### Concept
The local marketplace allows distributing ready-to-use accelerators (patterns, templates, workflows and hooks). Each item is described in `docs/marketplace_catalog.json` and can be installed via CLI:

```bash
ce marketplace list
ce marketplace install pattern_api_gateway --project-dir .
```

### Item Structure
```json
{
  "id": "pattern_auth_jwt_fastapi",
  "name": "JWT Auth for FastAPI",
  "description": "Complete JWT authentication blueprint",
  "source": "patterns/authentication/jwt-fastapi.md",
  "target_dir": "marketplace/patterns",
  "stack": ["python-fastapi"],
  "category": "security"
}
```

- **source**: relative path in the repository.
- **target_dir**: subfolder created inside the project when installing.
- **stack** (optional): recommended stacks.
- **category**: asset type.

### How to Publish a New Item
1. Create the asset (e.g.: `patterns/<category>/new.md` or `templates/prd/...`).
2. Update `docs/marketplace_catalog.json` adding a new object with unique `id`.
3. Document the item (e.g.: link in README or in `docs/MARKETPLACE.md`).
4. Open PR for review. After merge, users can run:
   ```bash
   ce marketplace install <id> --project-dir .
   ```

### Available Items
- `pattern_api_gateway` – REST blueprint with rate limiting.
- `hook_ci_traceability` – GitHub Actions workflow with commits.json.
- `pattern_auth_jwt_fastapi` – complete JWT authentication in FastAPI.
- `prd_template_saas` – base PRD for B2B SaaS products.

### Roadmap
- `ce marketplace publish` command pointing to a remote repository.
- Support for versioning/signatures for externally distributed assets.

---

## Referência em Português

### Conceito
O marketplace local permite distribuir aceleradores prontos (padrões, templates, workflows e hooks). Cada item é descrito em `docs/marketplace_catalog.json` e pode ser instalado via CLI:

```bash
ce marketplace list
ce marketplace install pattern_api_gateway --project-dir .
```

### Estrutura de um Item
```json
{
  "id": "pattern_auth_jwt_fastapi",
  "name": "JWT Auth for FastAPI",
  "description": "Blueprint completo de autenticação JWT",
  "source": "patterns/authentication/jwt-fastapi.md",
  "target_dir": "marketplace/patterns",
  "stack": ["python-fastapi"],
  "category": "security"
}
```

- **source**: caminho relativo no repositório.
- **target_dir**: subpasta criada dentro do projeto ao instalar.
- **stack** (opcional): stacks recomendadas.
- **category**: tipo de ativo.

### Como Publicar um Novo Item
1. Crie o ativo (ex.: `patterns/<categoria>/novo.md` ou `templates/prd/...`).
2. Atualize `docs/marketplace_catalog.json` adicionando um novo objeto com `id` único.
3. Documente o item (ex.: link no README ou em `docs/MARKETPLACE.md`).
4. Abra PR para revisão. Após merge, os usuários podem rodar:
   ```bash
   ce marketplace install <id> --project-dir .
   ```

### Itens Disponíveis
- `pattern_api_gateway` – blueprint REST com rate limiting.
- `hook_ci_traceability` – workflow GitHub Actions com commits.json.
- `pattern_auth_jwt_fastapi` – autenticação JWT completa em FastAPI.
- `prd_template_saas` – PRD base para produtos SaaS B2B.

### Roadmap
- Comando `ce marketplace publish` apontando para um repositório remoto.
- Suporte a versionamento/assinaturas para ativos distribuídos externamente.

---

## Referências de Código / Code References

Esta seção mapeia a funcionalidade do marketplace para os módulos de implementação correspondentes.

### Módulos Core

| Componente | Arquivo | Descrição | Métodos Principais |
|------------|---------|-----------|-------------------|
| **Marketplace Service** | `core/marketplace_service.py` | Gerencia catálogo, listagem e instalação de aceleradores | `load_catalog()`, `find_item()`, `copy_resource()` |
| **Pattern Library** | `core/engine.py` | Biblioteca de padrões reutilizáveis integrada ao engine | `pattern_library.suggest_patterns()`, `pattern_library.get_pattern()` |

### Comandos CLI

| Comando | Arquivo | Função | Descrição |
|---------|---------|--------|-----------|
| `ce marketplace list` | `cli/commands/marketplace.py` | `marketplace()` subcomando `list` | Lista itens disponíveis com filtros por categoria/stack |
| `ce marketplace install` | `cli/commands/marketplace.py` | `marketplace()` subcomando `install` | Instala acelerador no projeto |
| `ce patterns list` | `cli/commands/patterns.py` | `patterns()` subcomando `list` | Lista padrões da biblioteca |
| `ce patterns show` | `cli/commands/patterns.py` | `patterns()` subcomando `show` | Exibe detalhes de um padrão |
| `ce patterns suggest` | `cli/commands/patterns.py` | `patterns()` subcomando `suggest` | Sugere padrões baseado no contexto do projeto |

### Estrutura do Catálogo

**Localização:** `docs/marketplace_catalog.json`

**Schema de Item:**
```json
{
  "id": "string (unique)",
  "name": "string",
  "description": "string",
  "source": "path/relative/to/repo",
  "target_dir": "destination/in/project",
  "stack": ["array", "of", "stacks"],
  "category": "string",
  "version": "semver (optional)",
  "author": "string (optional)"
}
```

### Fluxo de Instalação

```
User: ce marketplace install <item_id> --project-dir .
       ↓
CLI: cli/commands/marketplace.py
       ↓
Service: core/marketplace_service.py
       ↓
1. Load catalog (docs/marketplace_catalog.json)
2. Find item by id
3. Resolve source path (repo_root / item.source)
4. Copy to target (project_dir / item.target_dir)
5. Log installation
```

### Exemplos de Uso Programático

**Listar Itens do Marketplace:**
```python
from core.marketplace_service import MarketplaceService
from pathlib import Path

service = MarketplaceService(repo_root=Path("/path/to/context-engineer"))
items = service.load_catalog()

# Filtrar por categoria e stack
filtered = [
    item for item in items 
    if item.get("category") == "security" 
    and "python-fastapi" in item.get("stack", [])
]

for item in filtered:
    print(f"{item['id']}: {item['name']}")
```

**Instalar Acelerador:**
```python
from core.marketplace_service import MarketplaceService
from pathlib import Path

service = MarketplaceService(repo_root=Path("/path/to/context-engineer"))

# Buscar item por ID
item = service.find_item("pattern_auth_jwt_fastapi")

if item:
    # Copiar recurso para o projeto
    target_path = service.copy_resource(
        item=item,
        project_path=Path("./my-project")
    )
    print(f"Installed to: {target_path}")
else:
    print("Item not found in catalog")
```

**Sugerir Padrões:**
```python
from core.engine import ContextEngine

engine = ContextEngine(use_transformers=True)
suggestions = engine.pattern_library.suggest_patterns({
    "stack": ["python-fastapi"],
    "requirements": ["authentication", "jwt", "security"]
})

for pattern in suggestions:
    print(f"- {pattern['id']}: {pattern['relevance_score']}")
```

### Adicionar Novo Item ao Marketplace

**Passo a Passo:**

1. **Criar o Ativo**
   - Padrões: `patterns/<categoria>/<nome>.md`
   - Templates: `templates/<tipo>/<nome>.j2`
   - Hooks: `docs/examples/<nome>.sh` ou `.yaml`

2. **Atualizar Catálogo**
   
   Edite `docs/marketplace_catalog.json`:
   ```json
   {
     "id": "pattern_new_feature",
     "name": "New Feature Pattern",
     "description": "Complete implementation pattern for X",
     "source": "patterns/features/new-feature.md",
     "target_dir": "marketplace/patterns",
     "stack": ["python-fastapi", "node-react"],
     "category": "features",
     "version": "1.0.0",
     "author": "Your Name"
   }
   ```

3. **Documentar**
   
   Adicione entrada em `docs/MARKETPLACE.md` na seção "Itens Disponíveis"

4. **Testar Instalação**
   ```bash
   ce marketplace install pattern_new_feature --project-dir ./test-project
   ```

5. **Abrir PR**
   
   Submeta para revisão com:
   - Arquivo do ativo
   - Entrada no catálogo
   - Documentação atualizada
   - Testes (se aplicável)

### Categorias Suportadas

| Categoria | Descrição | Exemplos |
|-----------|-----------|----------|
| `authentication` | Padrões de autenticação e autorização | JWT, OAuth2, RBAC |
| `api-patterns` | Padrões de design de APIs | REST, GraphQL, gRPC |
| `security` | Padrões de segurança | OWASP, encryption, validation |
| `observability` | Monitoramento e logging | OpenTelemetry, metrics, traces |
| `testing` | Padrões de testes | Unit, integration, E2E |
| `ci-cd` | Pipelines e automação | GitHub Actions, GitLab CI |
| `templates` | Templates de documentos | PRD, PRP, Task templates |

### Integração com Busca Semântica

O marketplace integra-se com o sistema de busca semântica quando `--ai` está habilitado:

```python
# Busca semântica de padrões relevantes
cache = IntelligenceCache("./.cache", use_embeddings=True)
similar = cache.search_similar({
    "stack": ["python", "fastapi"],
    "requirements": ["authentication", "jwt"],
    "project": "my-api"
}, limit=5)
```

### Estrutura de Arquivos

```
context-engineer/
├── docs/
│   └── marketplace_catalog.json      # Catálogo central
├── patterns/
│   ├── api-patterns/
│   │   └── restful-crud.md          # Padrão de API REST
│   └── authentication/
│       └── jwt-fastapi.md           # Padrão JWT FastAPI
├── templates/
│   └── base/
│       └── phases/*.j2               # Templates de fases
├── cli/commands/
│   ├── marketplace.py                # Comandos marketplace
│   └── patterns.py                   # Comandos patterns
└── core/
    ├── marketplace_service.py        # Serviço marketplace
    └── engine.py                     # Pattern library

```

### Testes

**Localização:** `tests/test_marketplace_service.py`

**Cobertura:**
- Listagem de itens com filtros
- Instalação de aceleradores
- Validação de catálogo
- Resolução de caminhos
- Sugestão de padrões

### Documentação Relacionada

- **Padrões Disponíveis:** `patterns/` (arquivos Markdown)
- **Stacks Suportadas:** `stacks/*.yaml`
- **Exemplos de Uso:** `docs/QUICK_REFERENCE.md` seção "Biblioteca de Padrões"
- **Arquitetura:** `docs/INDEX.md` seção "Stacks e Padrões Disponíveis"
