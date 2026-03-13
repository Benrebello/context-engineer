# title: F6 — APIs & Contracts
# description: Executable workflow per PRP phase
# steps:
- Load context from `.ide-rules/prompts/AGENTS.md`, `.ide-rules/prompts/PROJECT_STANDARDS.md`, `.ide-rules/prompts/GLOBAL_ENGINEERING_RULES.json`
- Expand `PRPs/openapi.yaml` with FR-* endpoints and examples
- Generate route stubs and DTOs with minimum roles/rate-limit requirements
- Run contract + unit tests; report results and produce diffs
- Update `PRPs/03_api_contracts.json`
