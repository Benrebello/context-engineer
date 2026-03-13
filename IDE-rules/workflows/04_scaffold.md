# title: F4 — Architecture & Scaffolding
# description: Executable workflow per PRP phase
# steps:
- Load context from `.ide-rules/prompts/AGENTS.md`, `.ide-rules/prompts/PROJECT_STANDARDS.md`, `.ide-rules/prompts/GLOBAL_ENGINEERING_RULES.json`
- Propose 2–3 architecture options with trade-offs; pick one and create ADR `docs/adr/0001-arch-decision.md`
- Create structure: `backend/src`, `frontend/src`, `infra/`, `docs/adr/`
- Run setup (example: `uv venv && uv pip install fastapi uvicorn pydantic`)
- Generate minimal files (`backend/src/main.py` with `/health`) and diffs
- Run existing tests (if any) and capture results
- Update `PRPs/01_scaffold.json` with artifacts and commands
