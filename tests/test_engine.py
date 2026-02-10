"""Tests for core.engine module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.engine import ContextEngine


@pytest.fixture()
def engine(tmp_path):
    """Create a ContextEngine with temporary directories."""
    base = Path(__file__).parent.parent
    return ContextEngine(
        templates_dir=base / "templates",
        patterns_dir=base / "patterns",
        schemas_dir=base / "schemas",
        cache_dir=tmp_path / ".cache",
        use_transformers=False,
    )


class TestCompressLogContent:
    def test_compress_short_log(self, engine):
        content = "line1\nline2\nline3"
        result = engine._compress_log_content(content)
        assert "line3" in result

    def test_compress_long_log(self, engine):
        lines = [f"log line {i}" for i in range(200)]
        content = "\n".join(lines)
        result = engine._compress_log_content(content)
        assert "Compressed" in result
        assert "log line 199" in result


class TestCompressJsonMetrics:
    def test_compress_dict(self, engine):
        content = json.dumps({"key1": 1, "key2": 2, "key3": 3})
        result = engine._compress_json_metrics(content)
        assert result is not None
        parsed = json.loads(result)
        assert "summary" in parsed
        assert parsed["total_keys"] == 3

    def test_compress_invalid_json(self, engine):
        result = engine._compress_json_metrics("not json")
        assert result is None

    def test_compress_non_dict(self, engine):
        result = engine._compress_json_metrics(json.dumps([1, 2, 3]))
        assert result is None


class TestCompressMarkdownContent:
    def test_compress_headers(self, engine):
        content = "# Title\nSome text\n## Section\nMore text\n### Sub\nDetails"
        result = engine._compress_markdown_content(content)
        assert "# Title" in result
        assert "## Section" in result

    def test_compress_code_blocks(self, engine):
        content = "# Title\n```python\nprint('hello')\n```\nText"
        result = engine._compress_markdown_content(content)
        assert "```python" in result


class TestCompressFileContent:
    def test_log_file(self, engine):
        result = engine._compress_file_content("line1\nline2", Path("app.log"))
        assert "line2" in result

    def test_json_metrics_file(self, engine):
        content = json.dumps({"metric1": 42})
        result = engine._compress_file_content(content, Path("metrics.json"))
        assert "summary" in result.lower() or "metric1" in result

    def test_markdown_file(self, engine):
        result = engine._compress_file_content("# Title\nText", Path("README.md"))
        assert "# Title" in result

    def test_large_file_truncation(self, engine):
        content = "x" * 10000
        result = engine._compress_file_content(content, Path("data.txt"))
        assert "Compressed" in result
        assert len(result) < 10000

    def test_small_file_passthrough(self, engine):
        content = "small content"
        result = engine._compress_file_content(content, Path("data.txt"))
        assert result == content


class TestGenerateTasksWithPrps:
    def test_generate_tasks_json_prps(self, engine, tmp_path):
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.json").write_text(json.dumps({"phase": "F0", "objectives": ["Plan"]}), encoding="utf-8")
        output = tmp_path / "tasks"
        result = engine.generate_tasks(prps_dir=prps, output_dir=output)
        assert result["success"] is True

    def test_generate_tasks_md_prps(self, engine, tmp_path):
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.md").write_text("---\nphase: F0\nobjectives:\n  - Plan\n---\n# F0\n", encoding="utf-8")
        output = tmp_path / "tasks"
        result = engine.generate_tasks(prps_dir=prps, output_dir=output)
        assert result["success"] is True


class TestCheckDependencies:
    def test_check_valid_deps(self, engine, tmp_path):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({
            "task_id": "FR-001", "inputs": []
        }), encoding="utf-8")
        result = engine.check_dependencies(tasks)
        assert result["valid"] is True

    def test_check_missing_dep(self, engine, tmp_path):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({
            "task_id": "FR-001", "inputs": ["TASK.FR-999.md"]
        }), encoding="utf-8")
        result = engine.check_dependencies(tasks)
        assert result["valid"] is False
        assert any("FR-999" in e for e in result["errors"])


class TestContextEngineInit:
    def test_default_init(self):
        eng = ContextEngine(use_transformers=False)
        assert eng is not None
        assert eng.template_engine is not None
        assert eng.pattern_library is not None
        assert eng.validator is not None
        assert eng.cache is not None

    def test_custom_dirs(self, tmp_path):
        eng = ContextEngine(
            templates_dir=tmp_path / "templates",
            patterns_dir=tmp_path / "patterns",
            schemas_dir=tmp_path / "schemas",
            cache_dir=tmp_path / ".cache",
            use_transformers=False,
        )
        assert eng.cache_dir == tmp_path / ".cache"


class TestInitProject:
    def test_init_project_python_fastapi(self, engine, tmp_path):
        output = tmp_path / "new_project"
        result = engine.init_project(
            template="base",
            project_name="test-project",
            stack="python-fastapi",
            output_dir=output,
        )
        assert result["success"] is True
        assert len(result["created_files"]) > 0
        assert (output / "README.md").exists()
        assert (output / ".gitignore").exists()

    def test_init_project_node_react(self, engine, tmp_path):
        output = tmp_path / "node_project"
        result = engine.init_project(
            template="base",
            project_name="node-test",
            stack="node-react",
            output_dir=output,
        )
        assert result["success"] is True

    def test_init_project_creates_dirs(self, engine, tmp_path):
        output = tmp_path / "proj"
        result = engine.init_project(
            template="base",
            project_name="proj",
            stack="python-fastapi",
            output_dir=output,
        )
        assert "created_directories" in result

    def test_init_project_records_metrics(self, engine, tmp_path):
        output = tmp_path / "proj"
        result = engine.init_project(
            template="base",
            project_name="metrics-test",
            stack="python-fastapi",
            output_dir=output,
        )
        assert result["success"] is True


class TestGeneratePRD:
    def test_generate_prd(self, engine, tmp_path):
        input_file = tmp_path / "idea.md"
        input_file.write_text("# My Idea\nA task management app", encoding="utf-8")
        output = tmp_path / "prd_output"
        result = engine.generate_prd(input_file, output)
        assert isinstance(result, dict)
        assert result.get("success") is True


class TestGeneratePRPs:
    def test_generate_prps(self, engine, tmp_path):
        prd_file = tmp_path / "prd_structured.json"
        prd_file.write_text(json.dumps({"visao": "test", "requisitos_funcionais": []}), encoding="utf-8")
        output = tmp_path / "prps_output"
        result = engine.generate_prps(prd_file, output)
        assert isinstance(result, dict)
        assert result.get("success") is True


class TestGenerateTasks:
    def test_generate_tasks(self, engine, tmp_path):
        prps_dir = tmp_path / "PRPs"
        prps_dir.mkdir()
        (prps_dir / "F1_scaffold.md").write_text("# F1\n## Objectives\n- Scaffold", encoding="utf-8")
        output = tmp_path / "tasks_output"
        result = engine.generate_tasks(prps_dir=prps_dir, output_dir=output)
        assert isinstance(result, dict)


class TestCheckDependencies:
    def test_check_dependencies(self, engine, tmp_path):
        tasks_dir = tmp_path / "TASKs"
        tasks_dir.mkdir()
        task = {"task_id": "FR-001", "dependencies": []}
        (tasks_dir / "TASK.FR-001.json").write_text(json.dumps(task), encoding="utf-8")
        result = engine.check_dependencies(tasks_dir)
        assert isinstance(result, dict)
        assert "valid" in result


class TestSuggestPatterns:
    def test_suggest_patterns(self, engine):
        context = {"stack": ["python"], "requirements": ["authentication"]}
        suggestions = engine.suggest_patterns(context)
        assert isinstance(suggestions, list)


class TestRecordTaskCompletion:
    def test_record_task_completion(self, engine, tmp_path):
        task_file = tmp_path / "TASK.FR-001.json"
        task_data = {
            "task_id": "FR-001",
            "objective": "Test task",
            "steps": ["s1"],
        }
        task_file.write_text(json.dumps(task_data), encoding="utf-8")
        # record_task_completion returns None
        engine.record_task_completion(
            project_name="test-proj",
            task_file=task_file,
            success=True,
        )

    def test_record_task_completion_failure(self, engine, tmp_path):
        task_file = tmp_path / "TASK.FR-002.json"
        task_data = {
            "task_id": "FR-002",
            "objective": "Failing task",
            "steps": ["s1"],
        }
        task_file.write_text(json.dumps(task_data), encoding="utf-8")
        engine.record_task_completion(
            project_name="test-proj",
            task_file=task_file,
            success=False,
            rework=True,
        )

    def test_record_task_completion_md(self, engine, tmp_path):
        task_file = tmp_path / "TASK.FR-003.md"
        task_file.write_text(
            '---\ntask_id: FR-003\nobjective: MD task\n---\n# Task\n',
            encoding="utf-8",
        )
        engine.record_task_completion(
            project_name="test-proj",
            task_file=task_file,
            success=True,
        )


class TestRecordTaskCompletionAdvanced:
    def test_record_with_pattern_id(self, engine, tmp_path):
        task_file = tmp_path / "TASK.FR-010.json"
        task_data = {
            "task_id": "FR-010",
            "objective": "Pattern task",
            "steps": ["s1"],
            "metadata": {"used_pattern_id": "auth-jwt", "category": "security"},
        }
        task_file.write_text(json.dumps(task_data), encoding="utf-8")
        engine.record_task_completion(
            project_name="test-proj",
            task_file=task_file,
            success=True,
            rework=False,
        )

    def test_record_rework_with_category(self, engine, tmp_path):
        task_file = tmp_path / "TASK.FR-011.json"
        task_data = {
            "task_id": "FR-011",
            "objective": "Rework task",
            "steps": ["s1"],
            "category": "authentication",
        }
        task_file.write_text(json.dumps(task_data), encoding="utf-8")
        engine.record_task_completion(
            project_name="test-proj",
            task_file=task_file,
            success=True,
            rework=True,
        )

    def test_record_md_with_json_block(self, engine, tmp_path):
        task_file = tmp_path / "TASK.FR-012.md"
        content = '# Task\n```json\n{"task_id": "FR-012", "objective": "MD JSON", "steps": ["s1"]}\n```\n'
        task_file.write_text(content, encoding="utf-8")
        engine.record_task_completion(
            project_name="test-proj",
            task_file=task_file,
            success=True,
        )

    def test_record_md_unparseable(self, engine, tmp_path):
        task_file = tmp_path / "TASK.FR-013.md"
        task_file.write_text("# Just text, no JSON or YAML\nNothing here.", encoding="utf-8")
        engine.record_task_completion(
            project_name="test-proj",
            task_file=task_file,
            success=True,
        )

    def test_record_nonexistent_file(self, engine, tmp_path):
        task_file = tmp_path / "TASK.MISSING.json"
        engine.record_task_completion(
            project_name="test-proj",
            task_file=task_file,
            success=True,
        )


class TestCompressContext:
    def test_compress_context_empty(self, engine):
        result = engine.compress_context([])
        assert isinstance(result, dict)

    def test_compress_context_with_files(self, engine, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text("\n".join(f"line {i}" for i in range(200)), encoding="utf-8")

        json_file = tmp_path / "metrics.json"
        json_file.write_text(json.dumps({"key": "value", "nested": {"a": 1}}), encoding="utf-8")

        md_file = tmp_path / "README.md"
        md_file.write_text("# Title\n\n## Section 1\nContent\n\n## Section 2\nMore content", encoding="utf-8")

        result = engine.compress_context([log_file, json_file, md_file])
        assert isinstance(result, dict)

    def test_compress_context_with_project_name(self, engine, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("some content " * 100, encoding="utf-8")
        result = engine.compress_context([f], project_name="test-proj")
        assert isinstance(result, dict)
