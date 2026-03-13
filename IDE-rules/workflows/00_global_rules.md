# title: F0 — Global Rules Gate (Unified)
# description: Validate adherence to global rules/standards before running phases
# steps:
- Load `.ide-rules/prompts/AGENTS.md`, `.ide-rules/prompts/PROJECT_STANDARDS.md`, `.ide-rules/prompts/GLOBAL_ENGINEERING_RULES.json`
- Check priorities (critical > high > medium) and list applicable rules
- Validate baseline compliance (language, budgets, LGPD, DRY/SOLID, reuse)
