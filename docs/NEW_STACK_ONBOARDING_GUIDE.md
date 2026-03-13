# Guia de Onboarding - Adicionando Nova Stack

> **Language Navigation / Navegação**
> - [English Reference](#english-reference)
> - [Referência em Português](#referencia-em-portugues)

## English Reference

This guide is primarily written in Portuguese. It walks you through creating custom stack YAML files, wiring them into `templates/base/template.yaml`, updating `core/planning.py`, crafting Jinja2 templates per phase, and validating everything via `ce init`, `ce estimate-effort`, and stack-specific scaffolds (example: Go + Gin). See the Portuguese section for the full step-by-step instructions and code snippets; keep the functional flow diagram (`docs/assets/context_engineer_flow.mmd` / `.png`) handy when presenting the stack onboarding process.

---

## Referência em Português

Este guia explica como criar seu próprio arquivo `.yaml` de stack e templates `.j2` customizados para o Context Engineer.

---

## Objetivo

Permitir que qualquer desenvolvedor adicione suporte a uma nova stack tecnológica sem modificar o código core do framework.

---

## Pré-requisitos

- Conhecimento básico de YAML
- Conhecimento básico de Jinja2 (opcional, mas recomendado)
- Entendimento da estrutura do projeto que você quer suportar

---

## Passo a Passo

### Passo 1: Criar Arquivo de Stack

Crie um arquivo `stacks/<nome-da-stack>.yaml` seguindo o padrão:

```yaml
name: "minha-stack"
version: "1.0.0"
description: "Minha stack customizada com tecnologia X, Y, Z"

commands:
 init: "comando-para-inicializar-projeto"
 install: "comando-para-instalar-dependencias"
 dev: "comando-para-desenvolvimento"
 test: "comando-para-testes"
 lint: "comando-para-linting"
 format: "comando-para-formatação"
 type_check: "comando-para-type-checking" # Opcional
 build: "comando-para-build" # Opcional

structure:
 domain: "src/domain"
 application: "src/application"
 infrastructure: "src/infrastructure"
 interfaces: "src/interfaces"
 components: "src/components" # Se aplicável
 stores: "src/stores" # Se aplicável
 utils: "src/utils"
 tests_unit: "tests/unit"
 tests_integration: "tests/integration"

patterns:
 - "patterns/authentication/jwt-fastapi.md" # Referências a padrões existentes
 - "patterns/ui-components/form-validation.md"

dependencies:
 - "framework>=1.0.0"
 - "testing-library>=2.0.0"
```

### Passo 2: Adicionar Stack ao Template

Atualize `templates/base/template.yaml` para incluir sua stack:

```yaml
 stack:
 type: "enum"
 default: "python-fastapi"
 options: ["python-fastapi", "node-react", "vue3", "minha-stack"]
```

### Passo 3: Atualizar Mapa de Complexidade

Adicione sua stack ao mapa de complexidade em `core/planning.py`:

```python
stack_complexity_map = {
 "python-fastapi": 0.3,
 "node-react": 0.4,
 "vue3": 0.4,
 "minha-stack": 0.5, # Ajuste conforme complexidade
 # ...
}
```

### Passo 4: (Opcional) Criar Templates Customizados

Se sua stack precisa de templates específicos, crie em `templates/base/phases/`:

```jinja2
{# templates/base/phases/scaffold_minha_stack.md.j2 #}

# Scaffolding para {{ stack }}

## Comandos Executáveis

```bash
# Inicializar projeto
{{ stack_commands.init }}

# Instalar dependências
{{ stack_commands.install }}
```

## Estrutura

{% if stack_structure %}
```
{{ stack_structure.domain }}/
{{ stack_structure.application }}/
...
```
{% endif %}
```

---

## Exemplo Completo: Stack Go + Gin

### `stacks/go-gin.yaml`

```yaml
name: "go-gin"
version: "1.0.0"
description: "Go 1.21+ with Gin, GORM, and modern tooling"

commands:
 init: "go mod init github.com/user/project"
 install: "go mod download"
 dev: "go run cmd/server/main.go"
 test: "go test ./..."
 lint: "golangci-lint run"
 format: "gofmt -w ."
 type_check: "go vet ./..."
 build: "go build -o bin/server cmd/server/main.go"

structure:
 domain: "internal/domain"
 application: "internal/application"
 infrastructure: "internal/infrastructure"
 interfaces: "internal/interfaces"
 handlers: "internal/handlers"
 utils: "internal/utils"
 tests_unit: "tests/unit"
 tests_integration: "tests/integration"

patterns:
 - "patterns/authentication/jwt-fastapi.md" # Adaptar para Go

dependencies:
 - "github.com/gin-gonic/gin>=1.9.0"
 - "gorm.io/gorm>=1.25.0"
 - "github.com/golang-jwt/jwt/v5>=5.0.0"
```

### Atualizar `templates/base/template.yaml`

```yaml
options: ["python-fastapi", "node-react", "vue3", "go-gin"]
```

### Atualizar `core/planning.py`

```python
stack_complexity_map = {
 # ...
 "go-gin": 0.3, # Go é simples mas menos comum
}
```

---

## Validação

Após criar sua stack:

1. **Teste o comando init**:
 ```bash
 ce init --project-name teste --stack minha-stack
 ```

2. **Verifique se os comandos são injetados corretamente**:
 - Abra o PRP gerado (F1 - Scaffold)
 - Verifique se `{{ stack_commands.init }}` foi substituído pelo comando correto

3. **Teste a estimativa de esforço**:
 ```bash
 ce estimate-effort TASKs/TASK.FR-001.json --stack minha-stack
 ```

---

## Boas Práticas

### 1. Nomenclatura Consistente
- Use formato `linguagem-framework`: `python-fastapi`, `node-react`, `go-gin`
- Evite espaços ou caracteres especiais

### 2. Comandos Completos
- Forneça todos os comandos necessários (init, install, dev, test, lint, format)
- Use comandos que funcionam em WSL/Linux e Windows quando possível

### 3. Estrutura Padrão
- Siga Clean Architecture quando possível
- Mantenha consistência com outras stacks

### 4. Documentação
- Adicione comentários no YAML explicando comandos complexos
- Documente dependências importantes

---

## Troubleshooting

### Problema: Comandos não são injetados no template

**Solução**: Verifique se:
- O nome da stack no YAML corresponde ao usado em `--stack`
- O arquivo está em `stacks/<nome>.yaml`
- O `StackPluginManager` está carregando corretamente

### Problema: Template não encontra stack_commands

**Solução**: Verifique se o template usa:
```jinja2
{% if stack_commands %}
{{ stack_commands.init }}
{% endif %}
```

### Problema: Estimativa de esforço muito alta/baixa

**Solução**: Ajuste o `stack_complexity` em `core/planning.py`:
- Valores menores (0.2-0.3) = mais simples
- Valores maiores (0.6-0.7) = mais complexo

---

## Recursos Adicionais

- **Stack Plugins**: Veja `core/stack_plugins.py` para entender como funciona
- **Templates**: Veja `templates/base/phases/` para exemplos de templates Jinja2
- **Stacks Existentes**: Consulte `stacks/python-fastapi.yaml` e `stacks/vue3.yaml` como referência

---

## Próximos Passos

Após criar sua stack:

1. Teste em um projeto real
2. Colete feedback sobre estimativas
3. Ajuste complexidade se necessário
4. Considere contribuir com a comunidade (PR)

---

## Dicas Avançadas

### Criar Padrões Específicos da Stack

Crie padrões em `patterns/<categoria>/<nome>-<stack>.md`:

```markdown
# Padrão: Autenticação JWT para Go/Gin

## Stack
- go
- gin

## Complexidade
medium

## Código
\`\`\`go
// Implementação aqui
\`\`\`
```

### Customizar Templates por Stack

Crie templates específicos:
- `templates/base/phases/scaffold_go_gin.md.j2`
- Use condicionais no template base:
```jinja2
{% if stack == "go-gin" %}
 {% include "phases/scaffold_go_gin.md.j2" %}
{% else %}
 {# Template padrão #}
{% endif %}
```

---

**Parabéns!** Você agora pode adicionar qualquer stack ao Context Engineer! 
