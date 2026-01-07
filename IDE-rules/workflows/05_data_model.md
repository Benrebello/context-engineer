# title: F5 — Data Model & Schemas
# description: Executable workflow per PRP phase
# steps:
- Load context from `.ide-rules/prompts/AGENTS.md`, `.ide-rules/prompts/PROJECT_STANDARDS.md`, `.ide-rules/prompts/GLOBAL_ENGINEERING_RULES.json`
- Derive entities/relationships from the PRD and propose the schema (ORM/SQL)
- Generate migrations, seeds, and schema tests; run and report results
- Produce diffs and update `PRPs/02_data_model.json`
