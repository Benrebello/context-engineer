# Efficiency Dashboard / Dashboard de Eficiência

> **Language Navigation / Navegação**
> - [English Reference](#english-reference)
> - [Referência em Português](#referencia-em-portugues)

---

## English Reference

### Overview

The `ce report` command provides a consolidated view of project health and the Context Engineer ecosystem.

### Available Formats

- **table** (default): textual output in terminal
- **json**: ideal for pipelines or external integrations
- **html**: creates a visual report with cards, risk colors and ROI sections

### Examples

```bash
# Visual dashboard for a specific project
ce report --project-name MyProject --format html --output dashboard_myproject.html

# Global dashboard filtering by stack
ce report --format html --stack python-fastapi --output dashboard_global.html
```

The HTML file can be opened in a browser or attached to executive reports.

---

## Referência em Português

### Visão Geral

O comando `ce report` fornece uma visão consolidada da saúde do projeto e do ecossistema Context Engineer.

### Formatos Disponíveis

- **table** (padrão): saída textual no terminal
- **json**: ideal para pipelines ou integrações externas
- **html**: cria um relatório visual com cartões, cores de risco e seções de ROI

### Exemplos

```bash
# Dashboard visual de um projeto específico
ce report --project-name MeuProjeto --format html --output dashboard_meuprojeto.html

# Dashboard global filtrando por stack
ce report --format html --stack python-fastapi --output dashboard_global.html
```

O arquivo HTML pode ser aberto no navegador ou anexado em relatórios executivos.
