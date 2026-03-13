# AGENTS — Global Operation (Unified)
- Assistant explanations must follow the **user-selected language (EN-US or PT-BR)**. Default: EN-US when unspecified.
- Code comments and docstrings: **EN-US** only.
- Budgets: API p95 ≤ 200 ms; frontend bundle ≤ 250 KB.
- Privacy/LGPD: no PII in logs, retention documented, explicit consent when required.
- Observability: JSON logs, OpenTelemetry tracing, maintained product event dictionary.
- Mandatory test coverage: unit, integration, contract suites.
- Always produce **complete diffs** and a **changelog** for every operation.

> This setup inherits the **Global Engineering Rules** from `.ide-rules/prompts/GLOBAL_ENGINEERING_RULES.json`.