# title: F1 — PRD Optimizer
# description: Convert the raw PRD into a 360° PRD + prd_structured.json (schema-validated)
# steps:
- Load `./.ide-rules/prompts/AGENTS.md`, `./.ide-rules/prompts/PROJECT_STANDARDS.md`, `./schemas/prd_structured.schema.json`
- Read the initial PRD (`./.ide-rules/docs/PRD_raw.md` or provided text)
- Rewrite `./PRD.md` with canonical sections and criteria per FR
- Generate `./prd_structured.json` and validate against the schema
- Check consistency Goals ⇄ Metrics ⇄ Criteria and FR⇄criteria coverage
- Add objective questions (max 8) at the end of `PRD.md`
