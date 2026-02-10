"""
UserStory Refiner Integration
Connects UserStory refinement to PRP pipeline
"""

import re


class UserStoryRefiner:
    """Refines Functional Requirements into formatted UserStories"""

    def refine_from_fr(self, fr: dict) -> dict:
        """
        Refine a Functional Requirement into formatted UserStory

        Args:
            fr: Functional Requirement dictionary

        Returns:
            Formatted UserStory dictionary
        """
        return {
            "id": fr.get("id", ""),
            "title": fr.get("title", ""),
            "as_a": self._extract_persona(fr),
            "i_want": self._extract_action(fr),
            "so_that": self._extract_value(fr),
            "acceptance_criteria": self._generate_acceptance_criteria(fr),
            "gherkin_scenarios": self._generate_gherkin(fr),
            "priority": fr.get("priority", "SHOULD"),
            "effort_points": fr.get("effort_points", 0),
        }

    def _extract_persona(self, fr: dict) -> str:
        """Extract persona from FR"""
        # Try to find persona in description or metadata
        description = fr.get("description", "")
        persona_match = re.search(r"(?:como|as)\s+([^,]+)", description, re.IGNORECASE)
        if persona_match:
            return persona_match.group(1).strip()
        return str(fr.get("persona", "usuário"))

    def _extract_action(self, fr: dict) -> str:
        """Extract desired action"""
        description = fr.get("description", "")
        # Try to find action pattern
        action_match = re.search(r"(?:quero|preciso|desejo)\s+(.+?)(?:,|\.|para|de forma)", description, re.IGNORECASE)
        if action_match:
            return action_match.group(1).strip()
        # Fallback to first sentence
        return description.split(",")[0].split(".")[0].strip()

    def _extract_value(self, fr: dict) -> str:
        """Extract business value"""
        description = fr.get("description", "")
        # Look for value patterns
        value_patterns = [
            r"(?:para que|de forma que|para)\s+(.+?)(?:\.|$)",
            r"(?:com o objetivo de|visando)\s+(.+?)(?:\.|$)",
        ]
        for pattern in value_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "melhorar experiência do usuário"

    def _generate_acceptance_criteria(self, fr: dict) -> list[str]:
        """Generate acceptance criteria"""
        criteria = fr.get("acceptance_criteria", [])
        if not criteria:
            # Generate basic criteria from description
            criteria = [
                f"O sistema deve permitir {fr.get('title', 'a funcionalidade')}",
                "A funcionalidade deve estar acessível e funcionar corretamente",
            ]
        return list(criteria)

    def _generate_gherkin(self, fr: dict) -> list[dict]:
        """Generate Gherkin scenarios from acceptance criteria"""
        scenarios = []
        criteria = self._generate_acceptance_criteria(fr)

        for i, criterion in enumerate(criteria, 1):
            scenario = {
                "scenario": f"Scenario {i}: {criterion}",
                "given": self._extract_given(criterion),
                "when": self._extract_when(criterion),
                "then": self._extract_then(criterion),
            }
            scenarios.append(scenario)

        return scenarios

    def _extract_given(self, criterion: str) -> str:
        """Extract Given clause from criterion"""
        # Look for Given patterns
        given_match = re.search(r"(?:dado|quando)\s+que\s+(.+?)(?:,|\.|quando)", criterion, re.IGNORECASE)
        if given_match:
            return given_match.group(1).strip()
        return "o sistema está funcionando"

    def _extract_when(self, criterion: str) -> str:
        """Extract When clause from criterion"""
        when_match = re.search(r"(?:quando|ao)\s+(.+?)(?:,|\.|então)", criterion, re.IGNORECASE)
        if when_match:
            return when_match.group(1).strip()
        return "o usuário realiza a ação"

    def _extract_then(self, criterion: str) -> str:
        """Extract Then clause from criterion"""
        then_match = re.search(r"(?:então|deve)\s+(.+?)(?:\.|$)", criterion, re.IGNORECASE)
        if then_match:
            return then_match.group(1).strip()
        return criterion


class TaskGenerator:
    """Generates Tasks from UserStories"""

    def __init__(self, userstory_refiner: UserStoryRefiner):
        self.refiner = userstory_refiner

    def generate_task_from_userstory(self, userstory: dict, prps: list[dict]) -> dict:
        """
        Generate TASK from UserStory

        Args:
            userstory: UserStory dictionary
            prps: List of PRP dictionaries for context

        Returns:
            Task dictionary
        """
        return {
            "task_id": userstory["id"],
            "objective": f"Implementar {userstory['title']}",
            "user_story": userstory,
            "inputs": self._determine_inputs(userstory, prps),
            "steps": self._generate_steps(userstory),
            "gherkin_scenarios": userstory["gherkin_scenarios"],
            "step_definitions": self._generate_step_definitions(userstory),
            "validation": self._generate_validation(userstory),
            "acceptance_criteria": userstory["acceptance_criteria"],
        }

    def _determine_inputs(self, userstory: dict, prps: list[dict]) -> list[str]:
        """Determine required inputs based on UserStory"""
        inputs = []

        # Always need PRPs
        for prp in prps:
            phase = prp.get("phase", "")
            if phase:
                inputs.append(f"PRPs/{phase}.md")

        # Add specific inputs based on UserStory content
        if "auth" in userstory.get("title", "").lower() or "login" in userstory.get("title", "").lower():
            inputs.append("PRPs/02_data_model.md")  # Need user model
            inputs.append("PRPs/08_security.md")  # Need security config

        return inputs

    def _generate_steps(self, _userstory: dict) -> list[str]:
        """Generate implementation steps"""
        return [
            "Analisar requisitos e critérios de aceitação",
            "Criar entidade de domínio se necessário",
            "Implementar caso de uso na camada de aplicação",
            "Criar endpoint/interface na camada de interfaces",
            "Implementar testes unitários",
            "Implementar testes de integração",
            "Adicionar testes BDD baseados em cenários Gherkin",
            "Validar critérios de aceitação",
            "Documentar implementação",
        ]

    def _generate_step_definitions(self, userstory: dict) -> list[dict]:
        """Generate step definitions for BDD tests"""
        step_defs = []
        for scenario in userstory.get("gherkin_scenarios", []):
            step_defs.append(
                {
                    "given": f"@given('{scenario['given']}')\ndef step_impl(context):\n # Implement step\n pass",
                    "when": f"@when('{scenario['when']}')\ndef step_impl(context):\n # Implement step\n pass",
                    "then": f"@then('{scenario['then']}')\ndef step_impl(context):\n # Implement step\n assert True",
                }
            )
        return step_defs

    def _generate_validation(self, _userstory: dict) -> list[dict]:
        """Generate validation commands"""
        return [
            {"tool": "tests", "command": "pytest tests/bdd/ -v", "expected": "all scenarios pass"},
            {
                "tool": "tests",
                "command": "pytest tests/unit/ -v --cov",
                "expected": "coverage >= 80%",
            },
            {"tool": "lint", "command": "ruff check .", "expected": "no errors"},
        ]
