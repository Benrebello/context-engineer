# title: F2 — PRP Compiler
# description: Compile prd_structured.json into PRPs + TASKs + openapi.yaml + execution_map.md
# steps:
- Load `./prd_structured.json`, `./.ide-rules/prompts/AGENTS.md`, `./.ide-rules/prompts/PROJECT_STANDARDS.md`
- Generate `./PRPs/00..09` (.md/.json) with context/objectives/inputs/outputs/steps/criteria/validations/risks/questions
- Include expected diffs (patch hints) whenever applicable
- Generate `./TASKs/TASK.FR-xxx.md/json` for every MUST FR (and relevant SHOULD ones)
- If an API exists: produce `./PRPs/openapi.yaml` covering the endpoints
- Generate `./execution_map.md` with order, commands, and gates
