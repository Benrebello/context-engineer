"""Tests for core.validators module."""

import json
from pathlib import Path

import pytest

from core.validators import PRPValidator, ValidationResult


@pytest.fixture()
def schemas_dir():
    return Path(__file__).parent.parent / "schemas"


@pytest.fixture()
def validator(schemas_dir):
    return PRPValidator(schemas_dir)


@pytest.fixture()
def sample_tasks_dir(tmp_path):
    """Create a minimal Tasks directory."""
    tasks = tmp_path / "TASKs"
    tasks.mkdir()
    task_data = {
        "task_id": "FR-001",
        "objective": "Implement user registration",
        "user_story": {"id": "US-001"},
        "steps": ["Create endpoint", "Add validation"],
        "validation": [{"tool": "pytest", "command": "pytest", "expected": "pass"}],
    }
    (tasks / "TASK.FR-001.json").write_text(
        json.dumps(task_data, indent=2), encoding="utf-8"
    )
    return tasks


class TestValidationResult:
    def test_valid(self):
        r = ValidationResult(True)
        assert r.valid is True
        assert bool(r) is True
        assert r.errors == []

    def test_invalid(self):
        r = ValidationResult(False, errors=["err1"])
        assert r.valid is False
        assert bool(r) is False
        assert len(r.errors) == 1

    def test_to_dict(self):
        r = ValidationResult(True, warnings=["warn1"])
        d = r.to_dict()
        assert d["valid"] is True
        assert d["warning_count"] == 1
        assert d["error_count"] == 0


class TestPRPValidator:
    def test_init_default_schemas(self):
        v = PRPValidator()
        assert v is not None

    def test_init_custom_schemas(self, schemas_dir):
        v = PRPValidator(schemas_dir)
        assert v is not None

    def test_extract_fr_ids(self, validator):
        content = "### FR-001 (MUST)\nDescription\n### FR-002 (SHOULD)\nAnother"
        ids = validator._extract_fr_ids(content)
        assert "FR-001" in ids
        assert "FR-002" in ids

    def test_extract_us_ids(self, validator):
        content = "US-001: As a user\nUS-002: As an admin"
        ids = validator._extract_us_ids(content)
        assert "US-001" in ids
        assert "US-002" in ids

    def test_validate_prp_missing_schema(self, validator, tmp_path):
        prp_file = tmp_path / "test.json"
        prp_file.write_text("{}", encoding="utf-8")
        result = validator.validate_prp(prp_file, schema_name="nonexistent-schema")
        assert isinstance(result, ValidationResult)
        assert result.valid is False

    def test_validate_prp_invalid_file(self, validator, tmp_path):
        prp_file = tmp_path / "bad.json"
        prp_file.write_text("not json", encoding="utf-8")
        result = validator.validate_prp(prp_file)
        assert isinstance(result, ValidationResult)
        assert result.valid is False

    def test_validate_dependencies_empty(self, validator):
        result = validator.validate_dependencies([])
        assert isinstance(result, ValidationResult)
        assert result.valid is True

    def test_validate_dependencies_with_files(self, validator, tmp_path):
        # Create PRP files with YAML frontmatter
        f0 = tmp_path / "F0.md"
        f0.write_text("---\nphase: F0\ndependencies: []\n---\n# F0\n", encoding="utf-8")
        f1 = tmp_path / "F1.md"
        f1.write_text("---\nphase: F1\ndependencies:\n  - F0\n---\n# F1\n", encoding="utf-8")
        result = validator.validate_dependencies([f0, f1])
        assert isinstance(result, ValidationResult)
        assert result.valid is True

    def test_validate_dependencies_missing_dep(self, validator, tmp_path):
        f1 = tmp_path / "F1.md"
        f1.write_text("---\nphase: F1\ndependencies:\n  - F0\n---\n# F1\n", encoding="utf-8")
        result = validator.validate_dependencies([f1])
        assert result.valid is False
        assert len(result.errors) >= 1

    def test_validate_consistency(self, validator):
        prd = {
            "functional_requirements": [
                {"id": "FR-001", "title": "Registration", "priority": "MUST"},
                {"id": "FR-002", "title": "Login", "priority": "SHOULD"},
            ]
        }
        prps = [{"content": "Implements FR-001 registration flow"}]
        result = validator.validate_consistency(prd, prps)
        assert isinstance(result, ValidationResult)

    def test_validate_consistency_missing_must(self, validator):
        prd = {
            "functional_requirements": [
                {"id": "FR-001", "title": "Registration", "priority": "MUST"},
            ]
        }
        prps = [{"content": "No FR references here"}]
        result = validator.validate_consistency(prd, prps)
        assert len(result.warnings) >= 1

    def test_load_file_json(self, validator, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        data = validator._load_file(f)
        assert data["key"] == "value"

    def test_load_file_yaml_frontmatter(self, validator, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\nphase: F0\n---\n# Content\n", encoding="utf-8")
        data = validator._load_file(f)
        assert data["phase"] == "F0"


class TestTraceability:
    def test_validate_traceability_full(self, validator, tmp_path):
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({
            "functional_requirements": [
                {"id": "FR-001", "title": "Registration", "priority": "MUST"},
                {"id": "FR-002", "title": "Login", "priority": "MUST"},
            ]
        }), encoding="utf-8")
        tasks = tmp_path / "TASKs"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({
            "task_id": "FR-001", "objective": "Registration",
        }), encoding="utf-8")
        (tasks / "TASK.FR-002.json").write_text(json.dumps({
            "task_id": "FR-002", "objective": "Login",
        }), encoding="utf-8")
        result = validator.validate_traceability(prd, tasks)
        assert isinstance(result, ValidationResult)
        assert result.valid is True

    def test_validate_traceability_missing_task(self, validator, tmp_path):
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({
            "functional_requirements": [
                {"id": "FR-001", "title": "Registration", "priority": "MUST"},
            ]
        }), encoding="utf-8")
        tasks = tmp_path / "TASKs"
        tasks.mkdir()
        result = validator.validate_traceability(prd, tasks)
        assert result.valid is False
        assert len(result.errors) >= 1

    def test_validate_traceability_orphaned_task(self, validator, tmp_path):
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({"functional_requirements": []}), encoding="utf-8")
        tasks = tmp_path / "TASKs"
        tasks.mkdir()
        (tasks / "TASK.FR-999.json").write_text(json.dumps({
            "task_id": "FR-999", "objective": "Orphan",
        }), encoding="utf-8")
        result = validator.validate_traceability(prd, tasks)
        assert len(result.warnings) >= 1

    def test_validate_acceptance_criteria(self, validator, tmp_path):
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({
            "functional_requirements": [
                {
                    "id": "FR-001", "title": "Reg", "priority": "MUST",
                    "acceptance_criteria": ["User can register with email"],
                },
            ]
        }), encoding="utf-8")
        tasks = tmp_path / "TASKs"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({
            "task_id": "FR-001", "objective": "Reg",
            "acceptance_criteria": ["User registers with email address"],
        }), encoding="utf-8")
        result = validator.validate_traceability(prd, tasks)
        assert isinstance(result, ValidationResult)


class TestValidateAll:
    def test_validate_all_basic(self, validator, tmp_path):
        prps = tmp_path / "PRPs"
        prps.mkdir()
        (prps / "F0.md").write_text("---\nphase: F0\n---\n# F0\n", encoding="utf-8")
        results = validator.validate_all(prps)
        assert isinstance(results, dict)
        assert "dependencies" in results

    def test_validate_all_with_prd(self, validator, tmp_path):
        prps = tmp_path / "PRPs"
        prps.mkdir()
        (prps / "F0.md").write_text("---\nphase: F0\n---\n# F0\n", encoding="utf-8")
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({"functional_requirements": []}), encoding="utf-8")
        results = validator.validate_all(prps, prd_file=prd)
        assert "consistency" in results

    def test_validate_all_with_prd_and_tasks(self, validator, tmp_path):
        prps = tmp_path / "PRPs"
        prps.mkdir()
        (prps / "F0.md").write_text("---\nphase: F0\n---\n# F0\n", encoding="utf-8")
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({"functional_requirements": []}), encoding="utf-8")
        tasks = tmp_path / "TASKs"
        tasks.mkdir()
        results = validator.validate_all(prps, prd_file=prd, tasks_dir=tasks)
        assert "traceability" in results


class TestContractValidation:
    def test_validate_contract_integrity_empty(self, validator, tmp_path):
        spec = tmp_path / "openapi.yaml"
        spec.write_text("openapi: '3.0.0'\ninfo:\n  title: Test\n  version: '1.0'\npaths: {}\n", encoding="utf-8")
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        result = validator.validate_contract_integrity(spec, tasks_dir)
        assert result is not None
        assert result.valid is True

    def test_validate_contract_with_endpoints(self, validator, tmp_path):
        spec = tmp_path / "openapi.json"
        spec.write_text(json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/api/users": {
                    "get": {"summary": "List users", "operationId": "listUsers"},
                    "post": {"summary": "Create user", "operationId": "createUser"},
                },
            },
        }), encoding="utf-8")
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "TASK.FR-001.md").write_text(
            "# Task\nGET /api/users\nPOST /api/users\n", encoding="utf-8"
        )
        result = validator.validate_contract_integrity(spec, tasks_dir)
        assert isinstance(result, ValidationResult)
        assert result.valid is True

    def test_validate_contract_broken_endpoint(self, validator, tmp_path):
        spec = tmp_path / "openapi.json"
        spec.write_text(json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/api/users": {
                    "get": {"summary": "List users"},
                },
            },
        }), encoding="utf-8")
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "TASK.FR-001.md").write_text(
            "# Task\nDELETE /api/nonexistent\n", encoding="utf-8"
        )
        result = validator.validate_contract_integrity(spec, tasks_dir)
        assert len(result.errors) >= 1

    def test_load_openapi_endpoints(self, validator, tmp_path):
        spec = tmp_path / "openapi.json"
        spec.write_text(json.dumps({
            "openapi": "3.0.0",
            "paths": {
                "/api/items/{id}": {
                    "get": {"summary": "Get item"},
                    "put": {"summary": "Update item"},
                },
            },
        }), encoding="utf-8")
        errors = []
        endpoints = validator._load_openapi_endpoints(spec, errors)
        assert len(errors) == 0
        assert len(endpoints) == 2


class TestTraceability:
    def test_traceability_all_covered(self, validator, tmp_path):
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({
            "functional_requirements": [
                {"id": "FR-001", "title": "Login", "priority": "MUST", "acceptance_criteria": ["User can login"]},
            ]
        }), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({
            "task_id": "FR-001",
            "acceptance_criteria": ["User can login with email"],
        }), encoding="utf-8")
        result = validator.validate_traceability(prd, tasks)
        assert result.valid is True

    def test_traceability_missing_task(self, validator, tmp_path):
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({
            "functional_requirements": [
                {"id": "FR-001", "title": "Login", "priority": "MUST"},
                {"id": "FR-002", "title": "Register", "priority": "MUST"},
            ]
        }), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({"task_id": "FR-001"}), encoding="utf-8")
        result = validator.validate_traceability(prd, tasks)
        assert result.valid is False
        assert any("FR-002" in e for e in result.errors)

    def test_traceability_orphaned_task(self, validator, tmp_path):
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({
            "functional_requirements": [
                {"id": "FR-001", "title": "Login", "priority": "MUST"},
            ]
        }), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({"task_id": "FR-001"}), encoding="utf-8")
        (tasks / "TASK.FR-999.json").write_text(json.dumps({"task_id": "FR-999"}), encoding="utf-8")
        result = validator.validate_traceability(prd, tasks)
        assert any("FR-999" in w for w in result.warnings)

    def test_acceptance_criteria_not_covered(self, validator, tmp_path):
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({
            "functional_requirements": [
                {
                    "id": "FR-001",
                    "title": "Login",
                    "priority": "MUST",
                    "acceptance_criteria": ["User must authenticate via OAuth2 with MFA"],
                },
            ]
        }), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({
            "task_id": "FR-001",
            "acceptance_criteria": ["Simple login form"],
        }), encoding="utf-8")
        result = validator.validate_traceability(prd, tasks)
        assert len(result.warnings) >= 1


class TestValidateAll:
    def test_validate_all_with_prd_and_tasks(self, validator, tmp_path):
        prps = tmp_path / "prps"
        prps.mkdir()
        valid_prp = {"phase": "F0", "objectives": ["Plan"], "deliverables": [], "dependencies": []}
        (prps / "F0.json").write_text(json.dumps(valid_prp), encoding="utf-8")
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({
            "functional_requirements": [
                {"id": "FR-001", "title": "Login", "priority": "MUST"},
            ]
        }), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({"task_id": "FR-001"}), encoding="utf-8")
        results = validator.validate_all(prps, prd_file=prd, tasks_dir=tasks)
        assert "traceability" in results
        assert "consistency" in results

    def test_validate_all_no_prd(self, validator, tmp_path):
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.json").write_text(json.dumps({"phase": "F0", "objectives": ["Plan"], "deliverables": [], "dependencies": []}), encoding="utf-8")
        results = validator.validate_all(prps)
        assert "dependencies" in results
        assert "traceability" not in results


class TestContractFetchPatterns:
    def test_fetch_pattern_in_task(self, validator, tmp_path):
        spec = tmp_path / "openapi.json"
        spec.write_text(json.dumps({
            "openapi": "3.0.0",
            "paths": {
                "/api/items": {"get": {"summary": "List"}},
            },
        }), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.md").write_text(
            '# Task\nfetch("/api/items")\n', encoding="utf-8"
        )
        result = validator.validate_contract_integrity(spec, tasks)
        assert isinstance(result, ValidationResult)

    def test_contract_with_path_params(self, validator, tmp_path):
        spec = tmp_path / "openapi.json"
        spec.write_text(json.dumps({
            "openapi": "3.0.0",
            "paths": {
                "/api/users/{id}": {"get": {"summary": "Get user"}},
            },
        }), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.md").write_text(
            "# Task\nGET /api/users/123\n", encoding="utf-8"
        )
        result = validator.validate_contract_integrity(spec, tasks)
        assert isinstance(result, ValidationResult)


class TestLoadSchemasErrorPath:
    def test_corrupt_schema_file(self, tmp_path):
        """_load_schemas handles corrupt JSON schema files."""
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        (schemas / "bad.json").write_text("NOT JSON", encoding="utf-8")
        v = PRPValidator(schemas)
        # Should not raise, just print error
        assert "bad" not in v.schemas or v.schemas.get("bad") is None


class TestLoadTasksForTraceability:
    def test_load_md_tasks(self, validator, tmp_path):
        """Load tasks from markdown files."""
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.md").write_text("# TASK.FR-001\nSome content", encoding="utf-8")
        (tasks / "TASK.FR-002.json").write_text(
            json.dumps({"task_id": "FR-002"}), encoding="utf-8"
        )
        task_ids, task_data = validator._load_tasks_for_traceability(tasks)
        assert "FR-001" in task_ids
        assert "FR-002" in task_ids
        assert "FR-002" in task_data

    def test_load_tasks_with_error(self, validator, tmp_path):
        """Handles corrupt task files gracefully."""
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-003.json").write_text("INVALID", encoding="utf-8")
        task_ids, task_data = validator._load_tasks_for_traceability(tasks)
        assert "FR-003" not in task_ids


class TestConsistencyWithReferencedFRs:
    def test_referenced_fr_not_in_prd(self, validator):
        """FR referenced in PRPs but not in PRD triggers error."""
        prd = {"functional_requirements": [{"id": "FR-001", "title": "Login"}]}
        prps = [{"phase": "F1", "objectives": ["Implement FR-999"]}]
        result = validator.validate_consistency(prd, prps)
        # FR-999 not in PRD → should report error
        assert isinstance(result, ValidationResult)


class TestContractFetchWithFullUrl:
    def test_fetch_with_http_url(self, validator, tmp_path):
        """Fetch pattern with full HTTP URL."""
        spec = tmp_path / "openapi.json"
        spec.write_text(json.dumps({
            "openapi": "3.0.0",
            "paths": {"/api/data": {"get": {"summary": "Get data"}}},
        }), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.md").write_text(
            '# Task\nfetch("http://localhost:3000/api/data")\n', encoding="utf-8"
        )
        result = validator.validate_contract_integrity(spec, tasks)
        assert isinstance(result, ValidationResult)

    def test_fetch_with_unvalidated_api_path(self, validator, tmp_path):
        """Fetch referencing /api path not in spec triggers warning."""
        spec = tmp_path / "openapi.json"
        spec.write_text(json.dumps({
            "openapi": "3.0.0",
            "paths": {"/api/users": {"get": {"summary": "List"}}},
        }), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.md").write_text(
            '# Task\nfetch("/api/unknown-endpoint")\n', encoding="utf-8"
        )
        result = validator.validate_contract_integrity(spec, tasks)
        assert isinstance(result, ValidationResult)

    def test_contract_integrity_openapi_load_error(self, validator, tmp_path):
        """Contract integrity with corrupt OpenAPI spec."""
        spec = tmp_path / "openapi.json"
        spec.write_text("NOT JSON", encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        result = validator.validate_contract_integrity(spec, tasks)
        assert not result.valid

    def test_contract_future_exception(self, validator, tmp_path):
        """Contract validation handles future exceptions."""
        from unittest.mock import patch, MagicMock
        spec = tmp_path / "openapi.json"
        spec.write_text(json.dumps({
            "openapi": "3.0.0",
            "paths": {"/api/x": {"get": {"summary": "X"}}},
        }), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.md").write_text("# Task\nGET /api/x\n", encoding="utf-8")
        with patch.object(validator, "_validate_single_task_contract", side_effect=RuntimeError("boom")):
            result = validator.validate_contract_integrity(spec, tasks)
        assert isinstance(result, ValidationResult)


class TestMockServerPrismAvailable:
    def test_prism_available_but_fails(self, validator, tmp_path):
        """Mock server when prism is available but process exits."""
        from unittest.mock import patch, MagicMock
        spec = tmp_path / "openapi.yaml"
        spec.write_text("openapi: '3.0.0'\ninfo:\n  title: Test\n  version: '1.0'\npaths: {}\n", encoding="utf-8")
        mock_run = MagicMock()
        mock_run.returncode = 0
        mock_popen = MagicMock()
        mock_popen.poll.return_value = 1  # Process exited
        mock_popen.communicate.return_value = ("", "error msg")
        with patch("subprocess.run", return_value=mock_run), \
             patch("subprocess.Popen", return_value=mock_popen), \
             patch("time.sleep"):
            result = validator.generate_transient_mock(spec, port=4010)
        assert not result["success"]
        assert "falhou" in result["errors"][0].lower() or "error" in result["errors"][0].lower()

    def test_prism_available_and_running(self, validator, tmp_path):
        """Mock server when prism starts successfully."""
        from unittest.mock import patch, MagicMock
        spec = tmp_path / "openapi.yaml"
        spec.write_text("openapi: '3.0.0'\ninfo:\n  title: Test\n  version: '1.0'\npaths: {}\n", encoding="utf-8")
        mock_run = MagicMock()
        mock_run.returncode = 0
        mock_popen = MagicMock()
        mock_popen.poll.return_value = None  # Still running
        mock_popen.pid = 12345
        with patch("subprocess.run", return_value=mock_run), \
             patch("subprocess.Popen", return_value=mock_popen), \
             patch("time.sleep"):
            result = validator.generate_transient_mock(spec, port=4010)
        assert result["success"]
        assert result["mock_url"] == "http://localhost:4010"
        assert result["process_id"] == 12345

    def test_prism_popen_exception(self, validator, tmp_path):
        """Mock server handles Popen exception."""
        from unittest.mock import patch, MagicMock
        spec = tmp_path / "openapi.yaml"
        spec.write_text("openapi: '3.0.0'\ninfo:\n  title: Test\n  version: '1.0'\npaths: {}\n", encoding="utf-8")
        mock_run = MagicMock()
        mock_run.returncode = 0
        with patch("subprocess.run", return_value=mock_run), \
             patch("subprocess.Popen", side_effect=OSError("cannot start")):
            result = validator.generate_transient_mock(spec, port=4010)
        assert not result["success"]


class TestMockServer:
    def test_generate_transient_mock_no_prism(self, validator, tmp_path):
        spec = tmp_path / "openapi.yaml"
        spec.write_text("openapi: '3.0.0'\ninfo:\n  title: Test\n  version: '1.0'\npaths: {}\n", encoding="utf-8")
        result = validator.generate_transient_mock(spec, port=4010)
        assert isinstance(result, dict)
        assert "success" in result
