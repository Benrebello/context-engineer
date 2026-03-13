# Context Engineer - CLI Workflow Diagrams

This document contains Mermaid diagrams visualizing the Context Engineer CLI workflows.

---

## Complete Pipeline Flow

```mermaid
graph TD
    A[Start] --> B{Project Initialized?}
    B -->|No| C[ce init]
    B -->|Yes| D{PRD Exists?}
    C --> D
    D -->|No| E[ce generate-prd]
    D -->|Yes| F{PRPs Exist?}
    E --> F
    F -->|No| F1[ce discuss phase]
    F1 --> G[ce generate-prps]
    F -->|Yes| H{Tasks Exist?}
    G --> H
    H -->|No| I[ce generate-tasks]
    H -->|Yes| J[ce validate]
    I --> J
    J --> K{Validation OK?}
    K -->|Yes| L[Implementation]
    K -->|No| M[Fix Issues]
    M --> J
    L --> L1[ce commit task]
    L1 --> L2[ce verify phase]
    L2 --> N[End]
```

---

## Autopilot Mode Flow

```mermaid
graph TD
    A[ce autopilot] --> B{Check Inputs}
    B --> C{Idea File?}
    C -->|Yes| D[Generate PRD]
    C -->|No| E{PRD File?}
    D --> F[Generate PRPs]
    E -->|Yes| F
    E -->|No| G{PRPs Dir?}
    F --> H[Generate Tasks]
    G -->|Yes| H
    G -->|No| I{Tasks Dir?}
    H --> J{Skip Validate?}
    I -->|Yes| J
    I -->|No| K[Error: No Input]
    J -->|No| L[ce validate]
    J -->|Yes| M[Complete]
    L --> N{Valid?}
    N -->|Yes| M
    N -->|No| O[Show Errors]
    O --> M
```

---

## Assistant/Wizard Flow

```mermaid
graph TD
    A[ce assist / ce wizard] --> B[Analyze Project State]
    B --> C{Init Complete?}
    C -->|No| D[Prompt: Run ce init?]
    C -->|Yes| E{PRD Complete?}
    D -->|Yes| F[Execute ce init]
    D -->|No| G[Skip]
    F --> E
    G --> E
    E -->|No| H[Prompt: Run ce generate-prd?]
    E -->|Yes| I{PRPs Complete?}
    H -->|Yes| J[Execute ce generate-prd]
    H -->|No| K[Skip]
    J --> I
    K --> I
    I -->|No| L[Prompt: Run ce generate-prps?]
    I -->|Yes| M{Tasks Complete?}
    L -->|Yes| N[Execute ce generate-prps]
    L -->|No| O[Skip]
    N --> M
    O --> M
    M -->|No| P[Prompt: Run ce generate-tasks?]
    M -->|Yes| Q[Show Summary]
    P -->|Yes| R[Execute ce generate-tasks]
    P -->|No| S[Skip]
    R --> Q
    S --> Q
    Q --> T[Display Next Steps]
    T --> U[End]
```

---

## Validation Flow

```mermaid
graph TD
    A[ce validate] --> B[Load PRPs]
    B --> C[Load PRD if provided]
    C --> D[Load Tasks if provided]
    D --> E[Validate Schema]
    E --> F{Schema Valid?}
    F -->|No| G[Report Schema Errors]
    F -->|Yes| H[Validate Consistency]
    H --> I{Consistent?}
    I -->|No| J[Report Consistency Errors]
    I -->|Yes| K[Validate Traceability]
    K --> L{PRD Provided?}
    L -->|Yes| M[Check PRD-PRP Mapping]
    L -->|No| N[Skip PRD Check]
    M --> O{Tasks Provided?}
    N --> O
    O -->|Yes| P[Check PRP-Task Mapping]
    O -->|No| Q[Skip Task Check]
    P --> R{Commits JSON?}
    Q --> R
    R -->|Yes| S[Check Task-Commit Mapping]
    R -->|No| T[Generate Report]
    S --> T
    T --> U{Soft Check?}
    U -->|Yes| V[Return with Warning]
    U -->|No| W{All Valid?}
    W -->|Yes| X[Success]
    W -->|No| Y[Fail with Errors]
```

---

## AI Governance Decision Flow

```mermaid
graph TD
    A[Command with --ai flag] --> B{--ai flag set?}
    B -->|--ai| C[Enable AI Mode]
    B -->|--no-ai| D[Disable AI Mode]
    B -->|Not set| E[Check Project Config]
    C --> F{Transformers Available?}
    D --> G[Use Levenshtein Mode]
    E --> H{Config has use_transformers?}
    H -->|Yes| I{Value is true?}
    H -->|No| J[Prompt User]
    I -->|Yes| F
    I -->|No| G
    J -->|Install| K[Install Dependencies]
    J -->|Skip| G
    F -->|Yes| L[Load Embedding Model]
    F -->|No| M[Prompt to Install]
    K --> L
    M -->|Install| K
    M -->|Skip| G
    L --> N{Model Specified?}
    N -->|Yes| O[Use Specified Model]
    N -->|No| P[Use Default Model]
    O --> Q[AI Mode Active]
    P --> Q
    G --> R[Light Mode Active]
```

---

## Marketplace Installation Flow

```mermaid
graph TD
    A[ce marketplace install ITEM_ID] --> B[Load Catalog]
    B --> C{Item Found?}
    C -->|No| D[Error: Item Not Found]
    C -->|Yes| E[Check Source Path]
    E --> F{Source Exists?}
    F -->|No| G[Error: Source Missing]
    F -->|Yes| H[Resolve Target Directory]
    H --> I[Create Target Directory]
    I --> J[Copy Resource]
    J --> K{Copy Success?}
    K -->|No| L[Error: Copy Failed]
    K -->|Yes| M[Log Installation]
    M --> N[Display Success Message]
    N --> O[End]
```

---

## Pattern Suggestion Flow

```mermaid
graph TD
    A[ce patterns suggest] --> B[Analyze Project]
    B --> C[Extract Context]
    C --> D{AI Mode?}
    D -->|Yes| E[Load Embedding Model]
    D -->|No| F[Use Levenshtein]
    E --> G[Generate Query Embedding]
    G --> H[Search Similar Patterns]
    F --> I[String Similarity Search]
    H --> J[Rank by Relevance]
    I --> J
    J --> K[Filter by Stack]
    K --> L[Filter by Category]
    L --> M[Return Top N]
    M --> N[Display Suggestions]
    N --> O[End]
```

---

## Git Hooks Flow (Soft-Gate)

```mermaid
graph TD
    A[git push] --> B[pre-push hook triggered]
    B --> C[ce validate --soft-check]
    C --> D{Validation Result?}
    D -->|Success| E[Allow Push]
    D -->|Failure| F[Display Errors]
    F --> G[Show Metrics Summary]
    G --> H[Explain Impact]
    H --> I[Prompt User]
    I -->|Continue| J[Allow Push with Warning]
    I -->|Abort| K[Block Push]
    J --> L[Log Decision]
    K --> L
    E --> M[End]
    L --> M
```

---

## CI/CD Bootstrap Flow

```mermaid
graph TD
    A[ce ci-bootstrap] --> B{Platform?}
    B -->|GitHub| C[Generate GitHub Actions YAML]
    B -->|GitLab| D[Generate GitLab CI YAML]
    C --> E[Create .github/workflows/]
    D --> F[Create .gitlab-ci.yml]
    E --> G[Write Workflow File]
    F --> G
    G --> H[Add Validation Steps]
    H --> I[Add Reporting Steps]
    I --> J[Add Artifact Upload]
    J --> K[Display Success]
    K --> L[Show Next Steps]
    L --> M[End]
```

---

## IDE Sync Flow

```mermaid
graph TD
    A[ce ide sync] --> B[Locate Context Engineer Repo]
    B --> C{Repo Found?}
    C -->|No| D[Error: Repo Not Found]
    C -->|Yes| E[Create .ide-rules/ Directory]
    E --> F[Copy Prompts]
    F --> G[Copy Workflows]
    G --> H[Copy Rules]
    H --> I[Copy Agents Config]
    I --> J{All Copied?}
    J -->|No| K[Warning: Partial Sync]
    J -->|Yes| L[Success Message]
    K --> M[List Missing Files]
    L --> N[Display Sync Summary]
    M --> N
    N --> O[End]
```

---

## Context Capture Flow

```mermaid
graph TD
    A["ce discuss phase_id"] --> B[Load PRP Data]
    B --> C{PRP Found?}
    C -->|No| D[Use Default Context]
    C -->|Yes| E[Analyze Phase]
    D --> E
    E --> F{Gray Areas Found?}
    F -->|No| G[Generate Empty CONTEXT.md]
    F -->|Yes| H{Batch Mode?}
    H -->|Yes| I[Show All Questions]
    H -->|No| J[Interactive One-by-One]
    I --> K[Collect Answers]
    J --> K
    K --> L[Generate CONTEXT.md]
    G --> M[Done]
    L --> M
```

---

## Health Check & Repair Flow

```mermaid
graph TD
    A["ce health"] --> B[Run Full Check]
    B --> C[Check Required Files]
    C --> D[Check STATE.json Integrity]
    D --> E[Check Constitution]
    E --> F[Check Git Health]
    F --> G[Check Planning Dir]
    G --> H{Issues Found?}
    H -->|No| I["All Checks Passed"]
    H -->|Yes| J{--repair flag?}
    J -->|No| K[Display Report]
    J -->|Yes| L[Auto-Fix Fixable Issues]
    L --> M[Display Actions Taken]
    K --> N[End]
    M --> N
    I --> N
```

---

## Session Management Flow

```mermaid
graph TD
    A{Session Command} -->|pause| B[Save Current State]
    A -->|resume| C[Load Saved State]
    A -->|status| D[Display Session Info]
    B --> E[Read STATE.json]
    E --> F[Create SESSION.json]
    F --> G["Display: Session Paused"]
    C --> H{SESSION.json Exists?}
    H -->|No| I[Error: No Session]
    H -->|Yes| J[Restore Context]
    J --> K["Display: Session Resumed"]
    D --> L{SESSION.json Exists?}
    L -->|No| M["No Active Session"]
    L -->|Yes| N[Show Session Details]
```

---

## Wave-Based Task Execution Flow

```mermaid
graph TD
    A[WaveExecutor] --> B[Parse Tasks]
    B --> C[Build Dependency Graph]
    C --> D[Topological Sort]
    D --> E{Circular Deps?}
    E -->|Yes| F[Error: Circular Dependency]
    E -->|No| G[Build Waves]
    G --> H["Wave 1: No Dependencies"]
    H --> I["Wave 2: Depends on Wave 1"]
    I --> J["Wave N: Final Tasks"]
    H --> K[Execute in Parallel]
    I --> K
    J --> K
    K --> L[Return Execution Plan]
```

---

## Verification & UAT Flow

```mermaid
graph TD
    A["ce verify phase_id"] --> B[Load PRP Data]
    B --> C{PRP Found?}
    C -->|No| D[Error: No PRP]
    C -->|Yes| E[Extract Deliverables]
    E --> F[Identify Test Scenarios]
    F --> G[Generate UAT Checklist]
    G --> H[Write UAT.md]
    H --> I[Display Summary]
    I --> J[End]
```

---

## Usage Instructions

To render these diagrams:

1. **In Markdown Viewers:**
   - GitHub, GitLab, and most modern Markdown viewers support Mermaid natively
   - Simply view this file in the web interface

2. **In VS Code:**
   - Install "Markdown Preview Mermaid Support" extension
   - Open this file and use Markdown preview

3. **Generate PNG/SVG:**
   ```bash
   # Using mermaid-cli
   npm install -g @mermaid-js/mermaid-cli
   mmdc -i cli-workflow-diagram.md -o cli-workflow-diagram.png
   ```

4. **Online Editor:**
   - Visit https://mermaid.live/
   - Copy and paste any diagram code

---

## Diagram Legend

- **Rectangle**: Process or action
- **Diamond**: Decision point
- **Rounded Rectangle**: Start/End point
- **Arrow**: Flow direction
- **Dashed Line**: Optional path
- **Bold Line**: Primary path

---

**Version:** 1.2  
**Last Updated:** 2026-03-13  
**Maintainer:** Context Engineer Team
