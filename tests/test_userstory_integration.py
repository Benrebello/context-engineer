"""Tests for core.userstory_integration module."""

from core.userstory_integration import TaskGenerator, UserStoryRefiner


class TestUserStoryRefiner:
    def test_init(self):
        refiner = UserStoryRefiner()
        assert refiner is not None

    def test_refine_from_fr_basic(self):
        refiner = UserStoryRefiner()
        fr = {
            "id": "FR-001",
            "title": "User Registration",
            "description": "User can register with email and password",
            "priority": "MUST",
        }
        story = refiner.refine_from_fr(fr)
        assert story is not None
        assert story["id"] == "FR-001"
        assert "as_a" in story
        assert "i_want" in story
        assert "so_that" in story
        assert "acceptance_criteria" in story
        assert "gherkin_scenarios" in story

    def test_refine_from_fr_with_persona(self):
        refiner = UserStoryRefiner()
        fr = {
            "id": "FR-002",
            "title": "Admin Management",
            "description": "As admin, quero manage users",
            "priority": "SHOULD",
            "persona": "administrator",
        }
        story = refiner.refine_from_fr(fr)
        assert story is not None
        assert story["priority"] == "SHOULD"

    def test_extract_persona_from_dict(self):
        refiner = UserStoryRefiner()
        fr = {"description": "Como admin, quero gerenciar usuarios"}
        persona = refiner._extract_persona(fr)
        assert isinstance(persona, str)
        assert len(persona) > 0

    def test_extract_persona_fallback(self):
        refiner = UserStoryRefiner()
        fr = {"description": "Simple feature", "persona": "developer"}
        persona = refiner._extract_persona(fr)
        assert persona == "developer"

    def test_extract_action(self):
        refiner = UserStoryRefiner()
        fr = {"description": "User quero register with email and password"}
        action = refiner._extract_action(fr)
        assert isinstance(action, str)

    def test_extract_action_fallback(self):
        refiner = UserStoryRefiner()
        fr = {"description": "Simple feature description"}
        action = refiner._extract_action(fr)
        assert isinstance(action, str)
        assert len(action) > 0

    def test_extract_value(self):
        refiner = UserStoryRefiner()
        fr = {"description": "User can login para que access their dashboard"}
        value = refiner._extract_value(fr)
        assert isinstance(value, str)

    def test_extract_value_fallback(self):
        refiner = UserStoryRefiner()
        fr = {"description": "Simple feature"}
        value = refiner._extract_value(fr)
        assert isinstance(value, str)

    def test_generate_acceptance_criteria_from_fr(self):
        refiner = UserStoryRefiner()
        fr = {"title": "User Registration", "description": "Register with email"}
        criteria = refiner._generate_acceptance_criteria(fr)
        assert isinstance(criteria, list)
        assert len(criteria) >= 1

    def test_generate_acceptance_criteria_existing(self):
        refiner = UserStoryRefiner()
        fr = {"acceptance_criteria": ["Criterion 1", "Criterion 2"]}
        criteria = refiner._generate_acceptance_criteria(fr)
        assert criteria == ["Criterion 1", "Criterion 2"]

    def test_generate_gherkin(self):
        refiner = UserStoryRefiner()
        fr = {"title": "Login", "description": "User can login"}
        scenarios = refiner._generate_gherkin(fr)
        assert isinstance(scenarios, list)
        assert len(scenarios) >= 1
        assert "scenario" in scenarios[0]
        assert "given" in scenarios[0]
        assert "when" in scenarios[0]
        assert "then" in scenarios[0]

    def test_extract_given(self):
        refiner = UserStoryRefiner()
        result = refiner._extract_given("dado que o sistema está pronto, quando clica")
        assert isinstance(result, str)

    def test_extract_when(self):
        refiner = UserStoryRefiner()
        result = refiner._extract_when("quando o usuario clica no botao, então vê resultado")
        assert isinstance(result, str)

    def test_extract_then(self):
        refiner = UserStoryRefiner()
        result = refiner._extract_then("então deve mostrar mensagem de sucesso")
        assert isinstance(result, str)


class TestTaskGenerator:
    def test_init(self):
        refiner = UserStoryRefiner()
        gen = TaskGenerator(refiner)
        assert gen is not None

    def test_generate_task_from_userstory(self):
        refiner = UserStoryRefiner()
        gen = TaskGenerator(refiner)
        story = {
            "id": "US-001",
            "title": "User Registration",
            "as_a": "user",
            "i_want": "to register",
            "so_that": "I can access the system",
            "acceptance_criteria": ["Given I am on the registration page"],
            "gherkin_scenarios": [
                {"scenario": "Successful registration", "given": "I am on the page", "when": "I submit", "then": "I see success"}
            ],
        }
        task = gen.generate_task_from_userstory(story, prps=[{"phase": "F1"}])
        assert task is not None
        assert task["task_id"] == "US-001"
        assert "objective" in task
        assert "steps" in task
        assert "validation" in task

    def test_determine_inputs(self):
        refiner = UserStoryRefiner()
        gen = TaskGenerator(refiner)
        story = {"title": "Auth Login"}
        prps = [{"phase": "F1"}, {"phase": "F3"}]
        inputs = gen._determine_inputs(story, prps)
        assert isinstance(inputs, list)
        assert any("F1" in i for i in inputs)

    def test_generate_steps(self):
        refiner = UserStoryRefiner()
        gen = TaskGenerator(refiner)
        steps = gen._generate_steps({})
        assert isinstance(steps, list)
        assert len(steps) > 0

    def test_generate_validation(self):
        refiner = UserStoryRefiner()
        gen = TaskGenerator(refiner)
        validation = gen._generate_validation({})
        assert isinstance(validation, list)
        assert len(validation) >= 1
        assert "tool" in validation[0]

    def test_generate_step_definitions(self):
        refiner = UserStoryRefiner()
        gen = TaskGenerator(refiner)
        story = {
            "gherkin_scenarios": [
                {"scenario": "Login", "given": "user exists", "when": "enters creds", "then": "sees dashboard"}
            ]
        }
        steps = gen._generate_step_definitions(story)
        assert isinstance(steps, list)
        assert len(steps) == 1
