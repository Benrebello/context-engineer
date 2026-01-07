# Governança de IA - Context Engineer

> **Language Navigation / Navegação**
> - [English Reference](#english-reference)
> - [Referência em Português](#referencia-em-portugues)

## English Reference

### Overview

This document details how the Context Engineer governance layer enforces traceability without blocking development. The Soft-Gate model plugs into terminal interaction tracks (`ce assist`, `ce status/checklist`, `ce wizard/autopilot/ci-bootstrap`) and mirrors the functional map described in `docs/assets/context_engineer_flow.mmd`. If your environment cannot render Mermaid, open the pre-generated PNG at `docs/assets/context_engineer_flow.png`.

### Terminal interaction tracks

| Track | Governance tie-in |
|-------|-------------------|
| **Conversational assistant** (`ce assist --format text|html`) | Surfaces AI Governance recommendations (patterns/cache, next focus) and can trigger validation-aware commands inline. |
| **Review/inspection** (`ce status`, `ce checklist`, `ce doctor [--ai-profile corporate]`, `ce ai-governance status`) | Shows completion metrics, blockers, ROI snapshots, Git hook diagnostics and applied AI profiles without prompting for actions; ideal for leadership checkpoints. |
| **Guided / automation** (`ce wizard`, `ce autopilot`, `ce ci-bootstrap`) | Wizard keeps developers in control, Autopilot runs unattended but still honors Soft-Gate policies, CI bootstrap wires `ce validate` + `ce report`. |

> All tracks honor `--ai/--no-ai`, `--ai-profile` presets and the embedding preferences resolved by `AIGovernanceService`, ensuring semantic vs. lightweight modes stay aligned with corporate policy.

### Diagram reference

- Mermaid source: `docs/assets/context_engineer_flow.mmd`
- PNG fallback: `docs/assets/context_engineer_flow.png`
- Optional render command: `npx @mermaid-js/mermaid-cli -i docs/assets/context_engineer_flow.mmd -o docs/assets/context_engineer_flow.png`

### What’s inside this document
1. Soft-Gate vs. Hard-Gate behavior, including hook installation commands.
2. How validation, ROI tracking, metrics summary, AI profiles (`--ai-profile`) and git hooks interact.
3. Programmatic extensions for `AIGovernanceService` (custom models, corporate policy providers).
4. Scenario-based walkthroughs (successful validation, Soft-Gate override, Hard-Gate block).

---

## Referência em Português

> A seção em inglês acima resume o conteúdo principal. O restante do documento mantém a descrição detalhada em português, preservando a arquitetura existente e referenciando tanto o arquivo Mermaid quanto o PNG pré-renderizado.

### Visão Geral

- Detalha como o Soft-Gate aplica governança sem travar o desenvolvimento.
- Integra-se às trilhas `ce assist`, `ce status/checklist`, `ce wizard/autopilot/ci-bootstrap`.
- Consulte `docs/assets/context_engineer_flow.mmd` (ou `context_engineer_flow.png`) para visualizar o fluxo completo.

**Status**: **Sistema de Soft-Gate Implementado**

---

## Objetivo

Implementar governança de IA sem travar o desenvolvimento, utilizando um sistema de **"Alerta e Consciência"** ao invés de bloqueios rígidos.

---

## Estratégia: Soft-Gate (Portão Suave)

O sistema de governança do Context Engineer utiliza uma abordagem **consultiva e apoiadora**:

1. **Executa validação completa** antes do push
2. **Exibe relatório visual claro** das inconsistências
3. **Solicita confirmação** ao desenvolvedor
4. **Permite prosseguir** em casos urgentes (hotfixes)
5. **Educa sobre impacto** da quebra de rastreabilidade

---

## Funcionalidades Implementadas

### 1. Git Hooks Consultivos (Soft-Gate)

**Arquivo**: `cli/main.py` - Função `_generate_git_hooks()`

**Modo Soft-Gate (Padrão)**:
- Mostra avisos sobre problemas de rastreabilidade
- Explica o impacto na capacidade da IA
- Solicita confirmação antes de prosseguir
- Permite continuar em casos urgentes

**Modo Hard-Gate (Opcional)**:
- Bloqueia push se validação falhar
- Use `--hard-gate` ao instalar hooks

**Uso**:
```bash
# Instalar hooks consultivos (padrão)
ce install-hooks

# Instalar hooks bloqueantes
ce install-hooks --hard-gate

# Instalar em projeto específico
ce install-hooks --project-dir ./meu-projeto
```

### 2. Comando `ce install-hooks`

**Arquivo**: `cli/main.py`

**Funcionalidades**:
- Detecta automaticamente projeto Git
- Gera hooks em `.git/hooks/`
- Suporta Soft-Gate (padrão) e Hard-Gate
- Detecta nome do projeto automaticamente

**Hooks Gerados**:
- **pre-commit**: Validação rápida de sintaxe JSON/YAML
- **pre-push**: Validação completa de rastreabilidade e contratos

### 3. Flag `--soft-check` no Validador

**Arquivo**: `cli/main.py` - Comando `validate`

**Funcionalidades**:
- Retorna código de erro mas não bloqueia execução
- Formatação visual melhorada de erros
- Resumo detalhado de problemas encontrados
- Usado automaticamente pelos Git hooks

**Uso**:
```bash
# Validação normal (bloqueia se falhar)
ce validate ./PRPs

# Validação consultiva (retorna erro mas permite continuar)
ce validate ./PRPs --soft-check
```

### 4. Relatório Visual Melhorado

**Melhorias**:
- Formatação clara com separadores visuais
- Contagem de erros e avisos
- Explicação do impacto de cada problema
- Resumo executivo no final

**Exemplo de Saída**:
```
 TRACEABILITY: 3 erro(s)
 ──────────────────────────────────────────────────────────────────────
 1. FR-02 não tem Task associada
 2. TASK.FR-001 referencia PRP inexistente
 3. Dependência circular detectada entre TASK.FR-003 e TASK.FR-004

 Avisos (2):
 1. Algumas tasks não têm estimativa de esforço
 2. Categoria 'security' tem alto histórico de rework

══════════════════════════════════════════════════════════════════════
 RESUMO DA VALIDAÇÃO
══════════════════════════════════════════════════════════════════════
 Erros encontrados: 3
 Avisos: 2
```

### 5. Tracking de ROI (Token Savings)

**Arquivo**: `core/metrics.py` - Métodos `record_context_pruning()` e `get_roi_metrics()`

**Funcionalidades**:
- Rastreia tokens economizados via Context Pruning
- Calcula custo estimado economizado (USD)
- Exibe métricas no dashboard `ce report`
- Aprende com histórico de compressão

### 6. Comando `ce metrics-summary` (Resumo Rápido)

**Arquivo**: `cli/main.py`

**Funcionalidades**:
- Exibe resumo compacto de métricas (Story Points, Rework Rate)
- Usado automaticamente pelo Git hook quando validação falha
- Fornece contexto quantitativo para decisão do desenvolvedor
- Calcula Story Points automaticamente se diretório de Tasks fornecido

**Uso Manual**:
```bash
# Resumo rápido de métricas
ce metrics-summary --project-name meu-projeto --tasks-dir ./TASKs
```

**Uso Automático**:
```python
# Tracking automático quando compress_context é chamado
engine.compress_context(files, project_name="meu-projeto")
# Métricas são registradas automaticamente
```

**Visualização**:
```bash
ce report --project-name meu-projeto

# Inclui seção:
 ROI - Economia de Tokens (Context Pruning):
 • Tokens economizados: 45,230
 • Tokens utilizados: 120,500
 • Taxa de economia: 37.5%
 • Eventos de pruning: 12
 • Custo estimado economizado: $2.45 USD
```

---

## Benefícios da Abordagem Soft-Gate

### 1. Apoio, Não Bloqueio
- Desenvolvedor é **avisado** sobre problemas
- Tem **palavra final** sobre prosseguir
- Mantém `git push --no-verify` disponível se necessário

### 2. Educação do Contexto
- Explica **por que** a rastreabilidade é importante
- Mostra **impacto** nas próximas fases (F5-F11)
- Reforça **boas práticas** sem ser intrusivo

### 3. Flexibilidade
- Permite **hotfixes urgentes** quando necessário
- Mantém **controle do desenvolvedor**
- Não quebra **workflows existentes**

### 4. Observabilidade
- Tracking de **ROI** (tokens economizados)
- Métricas de **eficiência** da IA
- **Dashboard** completo de governança

---

## Métricas de Governança

### Tracking Automático

O sistema rastreia automaticamente:

1. **Validações Executadas**: Quantas vezes hooks foram executados.
2. **Problemas Detectados**: Erros e avisos encontrados.
3. **Taxa de Aceitação**: Quantas vezes desenvolvedor prosseguiu apesar de avisos.
4. **ROI de Context Pruning**: Tokens economizados e custo estimado.
5. **Status dos Git Hooks**: Soft-Gate vs. Hard-Gate, instalações pendentes e última sincronização.

### Dashboard de Governança

```bash
# Ver métricas de governança
ce report --project-name meu-projeto

# Inclui:
# - Taxa de validação bem-sucedida
# - Problemas mais comuns
# - ROI de Context Pruning
# - Recomendações de melhoria
# - Snapshot de hooks (Soft-Gate/Hard-Gate) e status de instalação
```

---

## Configuração

### Instalação Padrão (Soft-Gate)

```bash
# No diretório do projeto
ce install-hooks

# Hooks são instalados em .git/hooks/
# Modo: Soft-Gate (consultivo)
```

### Instalação Hard-Gate (Bloqueante)

```bash
# Para ambientes que requerem bloqueio rígido
ce install-hooks --hard-gate

# Push será bloqueado se validação falhar
```

### Desabilitar Hooks Temporariamente

```bash
# Git nativo: pular hooks
git push --no-verify

# Ou remover hooks manualmente
rm .git/hooks/pre-push
```

---

## Exemplo de Fluxo

### Cenário 1: Validação Bem-Sucedida

```bash
$ git push

 Context Engineer: Validando rastreabilidade antes do push...

 Validando PRPs e rastreabilidade...
 TRACEABILITY: válido
 CONSISTENCY: válido
 DEPENDENCIES: válido

 Validação concluída com sucesso!

[Push continua normalmente]
```

### Cenário 2: Problemas Detectados (Soft-Gate)

```bash
$ git push

 Context Engineer: Validando rastreabilidade antes do push...

 Validando PRPs e rastreabilidade...
 TRACEABILITY: 2 erro(s)
 1. FR-02 não tem Task associada
 2. TASK.FR-001 referencia PRP inexistente

 ATENÇÃO: Foram encontradas inconsistências de rastreabilidade!

 Isso pode dificultar o trabalho da IA nas próximas fases (F5-F11).
 A quebra de rastreabilidade prejudica:
 • Context Pruning (compressão inteligente de contexto)
 • Deep Cross-Validation (detecção de broken contracts)
 • Estimativas precisas baseadas em histórico

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Contexto Quantitativo da Fase Atual:

 RESUMO DE MÉTRICAS DO PROJETO
──────────────────────────────────────────────────
 Story Points estimados: 34
 Taxa de retrabalho atual: 15.2%
 Taxa de conclusão: 78.5%
 Tasks: 11/14

 RISCO MODERADO: Taxa de retrabalho entre 15-30%
 Quebrar rastreabilidade pode aumentar ainda mais este risco.
──────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❓ Deseja prosseguir com o push mesmo assim? (y/n) y

 Prosseguindo com push (validação ignorada).
 Recomendação: Corrija os problemas antes do próximo push.

[Push continua]
```

**Novidade**: O hook agora mostra **dados quantitativos** (Story Points e Rework Rate) antes de solicitar confirmação, dando contexto ao desenvolvedor sobre o risco de prosseguir com rastreabilidade quebrada.

### Cenário 3: Problemas Detectados (Hard-Gate)

```bash
$ git push

 Context Engineer: Validando antes do push...

 Validando PRPs...
 Validação de PRPs falhou!
 Corrija os erros antes de fazer push.

[Push bloqueado]
```

---

## Impacto Esperado

### Antes (Sem Governança)
- Código sem rastreabilidade chega ao repositório
- Broken contracts detectados apenas em runtime
- Perda de contexto em projetos grandes
- Sem visibilidade de ROI

### Depois (Com Soft-Gate)
- **100% de código validado** antes do push
- **Educação contínua** sobre boas práticas
- **Flexibilidade** para casos urgentes
- **ROI visível** (tokens economizados)
- **Governança sem travar** desenvolvimento

---

## Documentação Relacionada

- **[REFINAMENTOS_FINAIS.md](REFINAMENTOS_FINAIS.md)** - Refinamentos DevOps
- **[MELHORIAS_NIVEL_SENIOR.md](MELHORIAS_NIVEL_SENIOR.md)** - Melhorias avançadas
- **[MAIN_USAGE_GUIDE.md](../MAIN_USAGE_GUIDE.md)** - Guia completo de uso
- **[docs/examples/ai_governance_policy.py](examples/ai_governance_policy.py)** - Script de referência para estender políticas corporativas

---

## Extensão do AIGovernanceService

`core/ai_governance_service.py` concentra decisões sobre preferências de IA e pode ser estendido para cenários corporativos.

### 1. Adicionar Modelos Personalizados

```python
from core.ai_governance_service import AIGovernanceService
from core.config_service import ProjectConfigService

custom_models = {
    "corp-mini": "contoso/corp-mini-embeddings",
    "corp-large": "contoso/corp-large-embeddings",
}

service = AIGovernanceService(
    config_service=ProjectConfigService(".ce-config.json"),
    available_models=custom_models,
)
```

- Use **aliases minúsculos** nas chaves e **identificadores completos** nos valores.
- Modelos adicionados aqui passam a ser aceitos pelos comandos `--embedding-model`.

### 2. Integrar Políticas Corporativas

```python
def corp_policy_provider():
    # Centralize leituras de feature flags ou vaults
    return os.getenv("ALLOW_TRANSFORMERS", "true").lower() == "true"

service = AIGovernanceService(
    config_service=ProjectConfigService(".ce-config.json"),
    transformers_available_provider=corp_policy_provider,
)
```

- Utilize o provider para conectar **catálogos internos**, **inventários de GPU** ou **listas de bloqueio**.
- O service continuará expondo `dependencies_ready()` para outras camadas.

### 3. Persistir Decisões de Política

```python
use_transformers, model, project_root, config = service.resolve_preferences(
    enable_ai=cli_flag,
    embedding_model=cli_model,
    context_hint=Path.cwd(),
)

if project_root:
    service.config_service.save_project_config(
        project_root,
        {
            "use_transformers": use_transformers,
            "embedding_model": model,
            "policy_source": "corp-governance",
        },
    )
```

- Registre no `.ce-config.json` metadados como **fonte da decisão**, **versão da política** ou **timestamp**.
- Esses campos adicionais são ignorados pelo core, permitindo que auditorias usem as mesmas informações.

### 4. Modo Somente-Light

Para desativar totalmente Transformers em ambientes sensíveis:

```python
service = AIGovernanceService(
    config_service=ProjectConfigService(".ce-config.json"),
    transformers_available_provider=lambda: False,
)
```

Isso garante que `check_intelligence_mode` nunca solicite instalação, mantendo o CLI em modo Leve.

### 5. Testar Suas Extensões

- Crie testes similares a `tests/test_ai_governance_service.py` ou `tests/test_cli_shared.py`.
- Faça mock do provider para simular diferentes centros de dados ou políticas.
- Use `CliRunner` para garantir que flags personalizadas se comportem conforme esperado.

---

## Status Final

| Funcionalidade | Status | Arquivo | Impacto |
|----------------|--------|---------|---------|
| **Soft-Gate Hooks** | Implementado | `cli/main.py` | Crítico |
| **Comando install-hooks** | Implementado | `cli/main.py` | Alto |
| **Flag --soft-check** | Implementado | `cli/main.py` | Alto |
| **Relatório Visual** | Implementado | `cli/main.py` | Médio |
| **ROI Tracking** | Implementado | `core/metrics.py` | Alto |
| **Metrics Summary** | Implementado | `cli/main.py` | Alto |

**Resultado**: Sistema de Governança de IA completo, consultivo e não intrusivo, com contexto quantitativo para decisões informadas!

---

## Referências de Código / Code References

Esta seção mapeia os conceitos de governança de IA descritos neste documento para os módulos de implementação correspondentes.

### Módulos Core de Governança

| Componente | Arquivo | Descrição | Métodos Principais |
|------------|---------|-----------|-------------------|
| **AI Governance Service** | `core/ai_governance_service.py` | Centraliza decisões sobre disponibilidade de transformers e modelos de embedding | `resolve_preferences()`, `dependencies_ready()`, `normalize_embedding_model()` |
| **Config Service** | `core/config_service.py` | Gerencia leitura/escrita de `.ce-config.json` | `load_project_config()`, `save_project_config()` |
| **Git Hook Manager** | `core/git_service.py` | Gera e instala hooks Git (pre-commit, pre-push) | Classe `GitHookManager` |
| **Metrics Collector** | `core/metrics.py` | Rastreia ROI, tokens economizados, rework rate | `record_context_pruning()`, `get_roi_metrics()` |

### Comandos CLI de Governança

| Comando | Arquivo | Função | Descrição |
|---------|---------|--------|-----------|
| `ce ai-governance status` | `cli/commands/ai_governance.py` | `ai_governance()` | Exibe status de governança, perfis de IA e políticas ativas |
| `ce doctor` | `cli/commands/doctor.py` | `doctor()` | Diagnóstico completo: hooks, IA, ROI, configurações |
| `ce install-hooks` | `cli/commands/devops.py` | `install_hooks()` | Instala Git hooks (Soft-Gate ou Hard-Gate) |
| `ce ci-bootstrap` | `cli/commands/devops.py` | `ci_bootstrap()` | Gera workflow GitHub Actions com validação |
| `ce metrics-summary` | `cli/commands/reporting.py` | `metrics_summary()` | Resumo rápido de métricas para decisões |
| `ce report` | `cli/commands/reporting.py` | `report()` | Dashboard completo com ROI e métricas |

### Fluxo de Decisão de IA

```
User Command (--ai/--no-ai, --embedding-model)
       ↓
AIGovernanceService.resolve_preferences()
       ↓
ConfigService.load_project_config() → .ce-config.json
       ↓
check_intelligence_mode() → TRANSFORMERS_AVAILABLE
       ↓
ContextEngine(use_transformers=X, embedding_model=Y)
```

### Configuração de Perfis de IA

Localização: `cli/shared.py` (linhas 39-59)

```python
AI_PROFILE_PRESETS = {
    "local": {
        "use_transformers": False,
        "embedding_model": "all-MiniLM-L6-v2",
        "auto_install_policy": "never"
    },
    "balanced": {
        "use_transformers": True,
        "embedding_model": "all-MiniLM-L6-v2",
        "auto_install_policy": "prompt"
    },
    "corporate": {
        "use_transformers": True,
        "embedding_model": "bge-small-en-v1.5",
        "auto_install_policy": "never",
        "policy_version": "corporate-1.0"
    }
}
```

### Git Hooks (Soft-Gate)

**Geração de Hooks:** `cli/shared.py` função `_generate_git_hooks()`

**Hooks Criados:**
- `pre-commit`: Validação rápida de sintaxe JSON/YAML
- `pre-push`: Validação completa com `ce validate --soft-check`

**Exemplo de Hook (pre-push):**
```bash
#!/bin/bash
ce validate ./prps --soft-check --project-name my-project
if [ $? -ne 0 ]; then
    echo "Deseja prosseguir? (y/n)"
    read response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi
```

### Tracking de ROI

**Implementação:** `core/metrics.py` (linhas 150-180)

**Métodos:**
- `record_context_pruning(tokens_saved, tokens_used, project_name)`
- `get_roi_metrics(project_name)` → retorna economia, taxa, custo estimado

**Uso Automático:**
```python
# Context Pruning registra automaticamente
engine.compress_context(files, project_name="my-project")
# Métricas disponíveis via:
metrics = collector.get_roi_metrics("my-project")
```

### Exemplos de Extensão

**1. Adicionar Modelo Customizado:**
```python
from core.ai_governance_service import AIGovernanceService
from core.config_service import ProjectConfigService

custom_models = {
    "corp-mini": "company/corp-mini-embeddings",
    "corp-large": "company/corp-large-embeddings"
}

service = AIGovernanceService(
    config_service=ProjectConfigService(".ce-config.json"),
    available_models=custom_models
)
```

**2. Política Corporativa:**
```python
def corp_policy_provider():
    # Integração com vault/feature flags
    return os.getenv("ALLOW_TRANSFORMERS", "true").lower() == "true"

service = AIGovernanceService(
    config_service=ProjectConfigService(".ce-config.json"),
    transformers_available_provider=corp_policy_provider
)
```

**3. Persistir Decisões:**
```python
use_ai, model, root, config = service.resolve_preferences(
    enable_ai=True,
    embedding_model="bge-small-en-v1.5",
    context_hint=Path.cwd()
)

if root:
    service.config_service.save_project_config(root, {
        "use_transformers": use_ai,
        "embedding_model": model,
        "policy_version": "v2.0",
        "audit_timestamp": datetime.now().isoformat()
    })
```

### Testes

**Localização:** `tests/test_ai_governance_service.py`, `tests/test_cli_ai_governance.py`

**Cobertura:**
- Resolução de preferências (CLI → config → defaults)
- Normalização de modelos de embedding
- Detecção de dependências
- Instalação de hooks
- Métricas de ROI

### Documentação Relacionada

- **Exemplo de Política:** `docs/examples/ai_governance_policy.py`
- **Configuração de Hooks:** `docs/REFINAMENTOS_FINAIS.md`
- **Métricas Avançadas:** `docs/MELHORIAS_NIVEL_SENIOR.md`
- **Fluxo Completo:** `docs/assets/context_engineer_flow.mmd` (ou `.png`)


