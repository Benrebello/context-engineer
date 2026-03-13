# PROJECT_STANDARDS — Stack & Quality (Adaptive)

> **Important:** This document defines **baseline standards** that adapt to your project's chosen stack. Standards are loaded from stack plugin files (`stacks/*.yaml`) and can be customized per project via `.ce-config.json`.

---

## Stack Integration

### How Standards Are Applied

1. **Stack Selection:** When initializing a project with `ce init`, you select a stack (e.g., `python-fastapi`, `node-react`, `go-gin`, `vue3`)
2. **Plugin Loading:** Context Engineer loads the corresponding stack plugin from `stacks/<stack-name>.yaml`
3. **Standards Adaptation:** Commands, structure, and tools adapt to the selected stack
4. **Project Customization:** Override standards in `.ce-config.json` for project-specific needs

### Available Stack Plugins

Context Engineer includes the following stack plugins:

| Stack | File | Description |
|-------|------|-------------|
| `python-fastapi` | `stacks/python-fastapi.yaml` | Python 3.11+ with FastAPI, SQLModel, modern tooling |
| `node-react` | `stacks/node-react.yaml` | Node.js 20+ with React, TypeScript, Vite, Tailwind |
| `go-gin` | `stacks/go-gin.yaml` | Go with Gin framework, GORM, modern Go tooling |
| `vue3` | `stacks/vue3.yaml` | Vue 3 with Composition API, TypeScript, Vite |

**Custom Stacks:** You can create custom stack plugins by adding new YAML files to the `stacks/` directory.

---

## Stack Plugin Structure

Each stack plugin defines:

```yaml
name: "stack-name"
version: "1.0.0"
description: "Stack description"

commands:
  init: "initialization command"
  install: "package installation"
  test: "test runner"
  lint: "linter command"
  format: "formatter command"
  type_check: "type checker"

structure:
  domain: "path/to/domain"
  application: "path/to/app"
  infrastructure: "path/to/infra"
  interfaces: "path/to/interfaces"

patterns:
  - "patterns/category/pattern.md"

dependencies:
  - "package>=version"
```

---

## Technology Stack Examples

### Python Stack (python-fastapi)
- **Version:** 3.11+
- **Package Manager:** uv / poetry
- **Web Framework:** FastAPI
- **ORM:** SQLModel / SQLAlchemy
- **Testing:** PyTest, pytest-cov (>= 80% coverage)
- **Linting:** Ruff
- **Formatting:** Black
- **Type Checking:** mypy (strict mode)
- **Server:** uvicorn

### JavaScript/TypeScript Stack (node-react)
- **Runtime:** Node 20+
- **Framework:** React 18+ / Next.js 14+
- **Styling:** Tailwind CSS
- **Build Tool:** Vite
- **Testing:** Vitest / Jest
- **Linting:** ESLint
- **Formatting:** Prettier
- **Type Checking:** TypeScript strict mode

### Go Stack (go-gin)
- **Version:** 1.21+
- **Framework:** Gin
- **ORM:** GORM
- **Testing:** Go test, testify
- **Linting:** golangci-lint
- **Formatting:** gofmt / goimports

### Vue Stack (vue3)
- **Runtime:** Node 20+
- **Framework:** Vue 3 (Composition API)
- **Styling:** Tailwind CSS
- **Build Tool:** Vite
- **Testing:** Vitest
- **Linting:** ESLint
- **Formatting:** Prettier

---

## Architecture

### Clean Architecture (Mandatory)
```
project/
├── domain/          # Business entities and rules
├── app/             # Use cases and application logic
├── infra/           # External services, databases, APIs
└── interfaces/      # Controllers, CLI, API endpoints
```

### Layer Dependencies
- `interfaces` → `app` → `domain`
- `infra` → `app` → `domain`
- Domain layer has NO dependencies

**Note:** Folder names adapt to your stack plugin. For example:
- Python: `src/domain`, `src/application`, `src/infrastructure`, `src/interfaces`
- Node/React: `src/domain`, `src/application`, `src/infrastructure`, `src/interfaces`
- Go: `internal/domain`, `internal/application`, `internal/infrastructure`, `internal/interfaces`

---

## Project Customization

### Per-Project Configuration (`.ce-config.json`)

Override default standards for your specific project:

```json
{
  "project_name": "my-api",
  "stack": "python-fastapi",
  "custom_commands": {
    "test": "pytest -v --cov --cov-report=html",
    "lint": "ruff check . --fix"
  },
  "custom_structure": {
    "domain": "src/core/domain",
    "application": "src/core/application"
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

### Stack-Specific Customization

Each stack can be customized by:
1. **Modifying stack plugin:** Edit `stacks/<stack-name>.yaml`
2. **Creating custom stack:** Copy existing stack and modify
3. **Project overrides:** Use `.ce-config.json` for project-specific changes

### Example: Custom Python Stack

Create `stacks/python-django.yaml`:
```yaml
name: "python-django"
version: "1.0.0"
description: "Python with Django, PostgreSQL, and Celery"

commands:
  init: "django-admin startproject"
  test: "python manage.py test"
  lint: "ruff check ."
  format: "black ."

structure:
  domain: "apps/domain"
  application: "apps/application"
  infrastructure: "apps/infrastructure"
  interfaces: "apps/api"

dependencies:
  - "django>=4.2.0"
  - "psycopg2-binary>=2.9.0"
  - "celery>=5.3.0"
```

Then use: `ce init my-project --stack python-django`

---

## Quality Gates

**Note:** Quality gates adapt to your stack's tooling. The following are baseline requirements that apply across all stacks.

### Pre-Commit (Mandatory)
- All linters pass (Ruff/ESLint)
- All formatters applied (Black/Prettier)
- Type checking passes (mypy/tsc)

### Pre-Merge (Mandatory)
- All tests pass (unit + integration)
- Code coverage >= 80%
- Contract tests pass (if applicable)
- No security vulnerabilities (Snyk/Dependabot)

---

## Commit Conventions

### Conventional Commits (Mandatory)
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes

### Branch Naming
- `feature/FR-XXX-description`
- `fix/bug-description`
- `refactor/component-name`

---

## Performance Budgets

**Note:** These are baseline recommendations. Adjust based on your project requirements in `.ce-config.json`.

### API (Backend Services)
- **p95 latency:** ≤ 200ms (customizable)
- **p99 latency:** ≤ 500ms (customizable)
- **Cold start:** ≤ 1s (serverless/containers)
- **Throughput:** Define based on expected load

**Stack-Specific Considerations:**
- **Python/FastAPI:** Async endpoints for I/O-bound operations
- **Node.js:** Event loop optimization, avoid blocking operations
- **Go:** Leverage goroutines for concurrency
- **Java/Spring:** Connection pooling, caching strategies

### Frontend (Web Applications)
- **Bundle size:** ≤ 250KB gzipped (customizable)
- **First Contentful Paint:** ≤ 1.5s
- **Time to Interactive:** ≤ 3.5s
- **Largest Contentful Paint:** ≤ 2.5s

**Stack-Specific Considerations:**
- **React/Vue:** Code splitting, lazy loading, tree shaking
- **Next.js:** SSR/SSG optimization, image optimization
- **Vite:** Optimized build configuration

### Customization Example
```json
{
  "performance_budgets": {
    "api_p95_ms": 150,
    "api_p99_ms": 300,
    "bundle_size_kb": 200,
    "fcp_seconds": 1.0
  }
}
```

---

## Security & Compliance

### LGPD/GDPR
- No PII in logs
- Data retention documented
- Explicit consent when required
- Data subject rights implemented

### Security
- No secrets in code
- Environment variables for config
- HTTPS only in production
- Rate limiting on public APIs

---

## Observability

### Logging
- JSON structured logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- No sensitive data in logs

### Tracing
- OpenTelemetry integration
- Distributed tracing for microservices

### Metrics
- Product event dictionary maintained
- KPIs tracked and dashboarded

---

## Code Review Guidelines

### Required Checks
- [ ] Follows Clean Architecture
- [ ] All tests passing
- [ ] Coverage >= 80%
- [ ] Linters/formatters applied
- [ ] No security vulnerabilities
- [ ] Performance budgets met
- [ ] Documentation updated
- [ ] Conventional commits used

### Review Focus
- Business logic correctness
- Error handling completeness
- Edge cases covered
- Code maintainability
- Performance implications

---

## How Agents Should Use This Document

### Adaptive Standards Application

**Context Engineer agents (PRD, PRP, Task) must:**

1. **Load Stack Configuration**
   - Read the project's stack from `.ce-config.json` or initialization parameters
   - Load corresponding stack plugin from `stacks/<stack-name>.yaml`
   - Apply stack-specific commands, structure, and dependencies

2. **Respect Project Overrides**
   - Check `.ce-config.json` for custom commands, structure, or quality overrides
   - Use project-specific values when available
   - Fall back to stack defaults when not specified

3. **Adapt, Don't Force**
   - **DO NOT** force Python-specific patterns on Node.js projects
   - **DO NOT** enforce FastAPI conventions on Django projects
   - **DO NOT** assume folder structure without checking stack plugin
   - **DO** adapt recommendations to the actual stack in use
   - **DO** suggest stack-appropriate patterns and libraries

4. **Generate Stack-Appropriate Code**
   - Use stack-specific syntax, idioms, and best practices
   - Reference stack-appropriate patterns from `patterns/` directory
   - Generate tests using stack-specific testing frameworks
   - Apply linting/formatting using stack-specific tools

### Example: Agent Behavior

**Scenario:** Generating authentication for a project

**Wrong Approach (Rigid):**
```python
# Always generates Python/FastAPI code regardless of stack
from fastapi import Depends
from jose import jwt
```

**Correct Approach (Adaptive):**
```python
# Agent checks stack first
if stack == "python-fastapi":
    # Generate FastAPI + JWT code
elif stack == "node-react":
    # Generate Express + JWT code
elif stack == "go-gin":
    # Generate Gin + JWT code
```

### Stack Plugin Integration

Agents should use the `StackPluginManager` from `core/stack_plugins.py`:

```python
from core.stack_plugins import StackPluginManager

# Load stack configuration
manager = StackPluginManager()
plugin = manager.load_plugin("python-fastapi")

# Use stack-specific commands
test_command = plugin.commands["test"]  # "pytest -v"
lint_command = plugin.commands["lint"]  # "ruff check ."

# Use stack-specific structure
domain_path = plugin.structure["domain"]  # "src/domain"
```

### Flexibility Guidelines

**Mandatory (Non-Negotiable):**
- Clean Architecture principles (domain/app/infra/interfaces separation)
- Test coverage >= 80% (customizable threshold)
- No PII in logs
- Conventional Commits format

**Flexible (Stack-Dependent):**
- Specific linters/formatters (Ruff vs ESLint)
- Testing frameworks (PyTest vs Vitest)
- Package managers (uv vs npm vs go mod)
- Folder naming conventions
- Performance budget values

**Customizable (Project-Specific):**
- Coverage thresholds
- Performance budgets
- Folder structure details
- Additional quality gates
- Custom commands

---

## Integration with Context Engineer CLI

Standards are automatically applied when using:

```bash
# Stack selection during init
ce init my-project --stack python-fastapi

# Stack info is saved to .ce-config.json
# All subsequent commands use stack-specific settings

ce generate-prps prd.json  # Uses python-fastapi commands
ce generate-tasks ./prps   # Generates Python-specific code
ce validate ./prps         # Uses pytest for validation
```

**Code References:**
- Stack Plugin Manager: `core/stack_plugins.py`
- Stack Plugin Schema: `schemas/stack_plugin.schema.yaml`
- Available Stacks: `stacks/*.yaml`
- Project Config: `.ce-config.json` (per project)
