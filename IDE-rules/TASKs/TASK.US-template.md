# TASK.US-XXX — Direct User Story Implementation

## User Story

**As a** [persona]  
**I want** [action]  
**So that** [business value]

---

## Acceptance Criteria

### Scenario 1: [Scenario name]
```gherkin
Given [initial condition]
When [user action]
Then [expected result]
And [additional outcome]
```

### Scenario 2: [Alternative scenario name]
```gherkin
Given [initial condition]
When [user action]
Then [expected result]
```

---

## XML Task Definition

```xml
{{ xml_representation }}
```

---

## Objective

Implement [clear, specific objective for the User Story] following Clean Architecture and ensuring all acceptance criteria pass.

---

## Context

- **Tech Stack**: defined in `PROJECT_STANDARDS.md`
- **Architecture**: Clean Architecture (domain/app/infra/interfaces)
- **Global Rules**: `GLOBAL_ENGINEERING_RULES.json`
- **Priority**: [MUST/SHOULD/COULD]

---

## Required Inputs

### Project Context
- `@GLOBAL_ENGINEERING_RULES.json` — Global rules
- `@PROJECT_STANDARDS.md` — Tech stack
- Existing codebase (inspect before writing code)

### Identified Dependencies
- [List of domain entities needed]
- [APIs or external services, if applicable]
- [Specific libraries or frameworks]

---

## Implementation Steps

1. **Analyze the User Story and identify domain entities**
   - Extract required entities
   - Identify relationships
   - Define value objects if needed

2. **Search the existing codebase**
   - Check whether entities already exist
   - Identify reusable services
   - Review established patterns

3. **Create/Update domain entity** (if needed)
   - Location: `src/domain/entities/[entity].py`
   - Include business validations
   - Document with docstrings

4. **Implement the use case in the application layer**
   - Location: `src/application/use_cases/[use_case].py`
   - Follow Service/UseCase conventions
   - Add error handling

5. **Expose an endpoint in the interfaces layer** (if applicable)
   - Location: `src/interfaces/api/[resource].py`
   - Follow RESTful conventions
   - Include input validation

6. **Implement BDD tests**
   - Location: `tests/bdd/[feature].feature`
   - Create step definitions
   - Cover every Gherkin scenario

7. **Implement unit tests**
   - Location: `tests/unit/[module]/test_[file].py`
   - Minimum coverage: 80%
   - Test both success and failure paths

8. **Add automated validations**
   - Lint: `ruff check .`
   - Formatting: `black --check .`
   - Tests: `pytest -q`

9. **Validate acceptance criteria**
   - Run BDD tests
   - Ensure all scenarios pass
   - Perform manual verification if needed

---

## Code to Implement

### Domain Entity (if needed)
```python
# src/domain/entities/[entity].py
# [Entity code]
```

### Use Case
```python
# src/application/use_cases/[use_case].py
# [Use case code]
```

### Endpoint (if applicable)
```python
# src/interfaces/api/[resource].py
# [Endpoint code]
```

### BDD Tests
```gherkin
# tests/bdd/[feature].feature
# [Gherkin scenarios]
```

### Step Definitions
```python
# tests/bdd/steps/[steps].py
# [Step definitions]
```

---

## BDD Tests (Gherkin)

### Feature: [Feature Name]
```gherkin
Feature: [Feature description]

  Scenario: [Main scenario]
    Given [initial condition]
    When [action]
    Then [expected result]

  Scenario: [Alternative scenario]
    Given [initial condition]
    When [different action]
    Then [expected result]
```

---

## Automated Validations

Run the following commands and confirm every check passes:

```bash
# Tests
pytest -q
# Expected: "0 failures"

# Linting
ruff check .
# Expected: "no errors"

# Formatting
black --check .
# Expected: "All done!"

# Coverage (if applicable)
pytest --cov=src --cov-report=term-missing
# Expected: "coverage >= 80%"
```

---

## Completion Criteria

- [ ] User Story fully implemented
- [ ] All acceptance criteria satisfied
- [ ] Code respects Clean Architecture
- [ ] BDD tests passing (all scenarios)
- [ ] Unit tests with coverage ≥ 80%
- [ ] Linting error-free
- [ ] Formatting OK
- [ ] Documentation (docstrings) updated
- [ ] Automated validations passing
- [ ] Code reuses existing components whenever possible

---

## Common Pitfalls

- **Do not duplicate entities**: always check if they already exist.  
+- **Do not skip validations**: run every command.  
!- **Do not skip BDD tests**: they confirm acceptance criteria.  
- **Do not break Clean Architecture**: respect layer boundaries.  
- **Do not forget documentation**: docstrings are mandatory.

---

## Additional Notes

[Space for implementation-specific observations]

---

**Status**: Pending implementation  
**Priority**: [MUST/SHOULD/COULD]  
**Estimate**: [story points or hours]

