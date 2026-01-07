# title: F3 — Alignment & Plan
# description: Executable workflow across PRP phases
# steps:
- Load context from `.ide-rules/prompts/AGENTS.md`, `.ide-rules/prompts/PROJECT_STANDARDS.md`, `.ide-rules/prompts/GLOBAL_ENGINEERING_RULES.json`
- Read PRD/PRPs (`PRPs/00_plan.md`), derive WBS (epics → features → tasks)
- Prioritize by value/risk (MoSCoW) and update `PRPs/00_plan.json`
- Map risks/assumptions and gates; raise objective questions for gaps
