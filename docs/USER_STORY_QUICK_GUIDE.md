# Guia Rápido - UserStory Direta

> **Language Navigation / Navegação**
> - [English Reference](#english-reference)
> - [Referência em Português](#referencia-em-portugues)
>
> **Language note:** `@Agente_Task_Direto.md` inherits the same language preference the user picked in `@Agente_PRD_360.md` (EN-US or PT-BR). Keep bilingual inputs ready so Tasks can mirror the selected language.

## English Reference

### 1. When to use this flow
- Choose the **User Story Direct** path when the Product team already produced a complete User Story (persona, action, value, acceptance criteria).
- Skip PRD/PRPs entirely; the agent goes straight to generating the Task instructions, code outline and tests.

### 2. Single-step process (IDE IDE)
```
@Agente_Task_Direto.md

UserStory:
As a [persona]
I want [action]
So that [business value]

Acceptance Criteria:
- Given [context]
- When [user action]
- Then [expected outcome]
```

> Tip: mention stack hints (e.g., “Stack: Python/FastAPI”) so the agent aligns templates and dependencies.

### 3. Recommended formats
- **Story template**: “As a [persona], I want [action], so that [value].”
- **Gherkin criteria**: Given / When / Then (+ optional And).

### 4. Practical examples
**Authentication**
```
UserStory:
As an unauthenticated user
I want to log in with email and password
So that I can access the product

Criteria:
- Given I am on the login page
- When I submit valid credentials
- Then I’m authenticated and redirected to the dashboard
- And I receive a JWT token

Stack: Python/FastAPI
```

**Paginated listing**
```
UserStory:
As an administrator
I want a paginated user list
So that I can manage access

Criteria:
- Given I am logged in as admin
- When I open the users page
- Then I see 10 users per page
- And I can go to the next page
- And I can filter by status

Stack: Python/FastAPI
```

### 5. Outputs you receive
1. `TASK.US-XXX.md` – implementation steps, guardrails, validation notes.
2. `TASK.US-XXX.json` – machine-readable metadata for automation.
3. Suggested code changes (domain entities, use cases, endpoints, tests).

### 6. Validation checklist
```bash
pytest -q
ruff check .
black --check .
```

### 7. Related files
- `.IDE/prompts/Agente_Task_Direto.md`
- `.IDE/TASKs/TASK.US-template.md`
- `.IDE/TASKs/TASK.US-template.json`

> **Release checklist**: When you finish implementing the task, follow the PyPI/GitHub Actions checklist detailed in [`docs/MAIN_USAGE_GUIDE.md#release-checklist-pypi--github-actions`](MAIN_USAGE_GUIDE.md#release-checklist-pypi--github-actions) to keep CI/CD, prompts and diagnostics aligned.

### 8. Comparison vs. full flow
| | Simplified Mode | Full Mode |
|---|---|---|
| Duration | 5-10 min | 30-60 min |
| Artifacts | Task only | PRD + PRPs + Tasks |
| Ideal for | Ready-made User Story | Raw idea |

---

## Referência em Português

### Uso Direto com UserStory

Este guia mostra como usar o Context Engineer **diretamente com UserStory**, pulando PRD/PRPs.

---

### Quando Usar

Use quando você **já tem UserStory formatada** e quer implementação rápida.

---

### Processo em 1 Passo

#### No IDE IDE:

```
@Agente_Task_Direto.md

UserStory:
Como um [persona]
Eu quero [ação]
Para que [valor]

Critérios de Aceitação:
- Dado que [condição]
- Quando [ação]
- Então [resultado]
```

**Pronto!** O agente gera Task completa e código funcional.

---

### Formato da UserStory

#### Formato Padrão:
```
Como um [persona específica]
Eu quero [ação clara]
Para que [valor de negócio]
```

#### Critérios em Gherkin:
```
- Dado que [condição inicial]
- Quando [ação do usuário]
- Então [resultado esperado]
- E [resultado adicional]
```

---

### Exemplos Práticos

#### Exemplo 1: Autenticação

```
@Agente_Task_Direto.md

UserStory:
Como um usuário não autenticado
Eu quero fazer login com email e senha
Para que eu possa acessar o sistema

Critérios:
- Dado que estou na página de login
- Quando preencho email e senha válidos
- Então sou autenticado com sucesso
- E sou redirecionado para o dashboard
- E recebo um token JWT

Stack: Python/FastAPI
```

#### Exemplo 2: Listagem

```
@Agente_Task_Direto.md

UserStory:
Como um administrador
Eu quero visualizar lista de usuários paginada
Para que eu possa gerenciar acessos

Critérios:
- Dado que estou autenticado como admin
- Quando acesso a página de usuários
- Então vejo 10 usuários por página
- E posso navegar para próxima página
- E posso filtrar por status

Stack: Python/FastAPI
```

---

### O que é Gerado

Após executar, você terá:

1. **TASK.US-XXX.md** - Task completa com:
   - Passos de implementação
   - Código a implementar
   - Testes BDD
   - Validações

2. **TASK.US-XXX.json** - Configuração da task

3. **Código implementado**:
   - Entidades de domínio
   - Casos de uso
   - Endpoints (se aplicável)
   - Testes

---

### Validação

Após gerar, execute:

```bash
# Testes
pytest -q

# Linting
ruff check .

# Formatação
black --check .
```

> **Checklist de release**: Quando estiver preparando deploy (PyPI ou GitHub Actions), siga a mesma lista de verificação descrita em [`docs/MAIN_USAGE_GUIDE.md#release-checklist-pypi--github-actions`](MAIN_USAGE_GUIDE.md#release-checklist-pypi--github-actions) para garantir sincronismo de prompts, diagnósticos (`ce doctor`, `ce ai-governance status`) e workflows (`ce ci-bootstrap`).

---

### Arquivos Relacionados

- **`.IDE/prompts/Agente_Task_Direto.md`** - Prompt principal
- **`.IDE/TASKs/TASK.US-template.md`** - Template de task
- **`.IDE/TASKs/TASK.US-template.json`** - Template JSON

---

### 🆚 Comparação com Modo Completo

| | Modo Simplificado | Modo Completo |
|---|---|---|
| **Tempo** | 5-10 min | 30-60 min |
| **Arquivos** | Apenas Task | PRD + PRPs + Tasks |
| **Quando** | UserStory pronta | Apenas ideia |

---

**Dica**: Use o modo simplificado para features isoladas e o modo completo para projetos novos!
