from pathlib import Path
from typing import Any

import click
import pytest

from core.autopilot_service import AutopilotService


class CommandRecorder:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def record(self, name: str) -> None:
        self.calls.append(name)


def _fake_invoker(command, **kwargs):
    command(**kwargs)


def _touch(path: Path, content: str = "{}") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_commands(recorder: CommandRecorder, project_path: Path) -> dict[str, Any]:
    def init_cmd(**kwargs):
        recorder.record("init")
        output = Path(kwargs["output"])
        output.mkdir(parents=True, exist_ok=True)
        _touch(output / ".ce-config.json")

    def generate_prd_cmd(**kwargs):
        recorder.record("generate_prd")
        output = Path(kwargs["output"])
        output.mkdir(parents=True, exist_ok=True)
        _touch(output / "prd_structured.json")

    def generate_prps_cmd(**kwargs):
        recorder.record("generate_prps")
        output = Path(kwargs["output"])
        output.mkdir(parents=True, exist_ok=True)
        _touch(output / "F0_plan.md", "phase content")

    def generate_tasks_cmd(**kwargs):
        recorder.record("generate_tasks")
        output = Path(kwargs["output"])
        output.mkdir(parents=True, exist_ok=True)
        _touch(output / "TASK.001.md", "task content")

    def validate_cmd(**kwargs):
        recorder.record("validate")

    return {
        "init": init_cmd,
        "generate_prd": generate_prd_cmd,
        "generate_prps": generate_prps_cmd,
        "generate_tasks": generate_tasks_cmd,
        "validate": validate_cmd,
    }


def test_run_flow_generates_missing_assets(tmp_path: Path) -> None:
    project_dir = tmp_path / "workspace"
    idea_file = tmp_path / "idea.md"
    idea_file.write_text("Nova feature com IA", encoding="utf-8")

    recorder = CommandRecorder()
    commands = _make_commands(recorder, project_dir)

    service = AutopilotService()
    result = service.run_flow(
        invoker=_fake_invoker,
        echo=lambda msg: None,
        project_path=project_dir,
        project_name="hyperion",
        stack="python-fastapi",
        idea_file=str(idea_file),
        prd_file=None,
        prps_dir=None,
        tasks_dir=None,
        skip_validate=False,
        tasks_from_us=False,
        enable_ai=None,
        embedding_model=None,
        init_command=commands["init"],
        generate_prd_command=commands["generate_prd"],
        generate_prps_command=commands["generate_prps"],
        generate_tasks_command=commands["generate_tasks"],
        validate_command=commands["validate"],
    )

    assert recorder.calls == [
        "init",
        "generate_prd",
        "generate_prps",
        "generate_tasks",
        "validate",
    ]
    assert result["prd_path"]
    assert Path(result["prd_path"]).exists()
    assert result["prps_path"]
    assert Path(result["prps_path"]).exists()
    assert result["tasks_path"]
    assert Path(result["tasks_path"]).exists()


def test_run_flow_respects_existing_inputs_and_skip_validate(tmp_path: Path) -> None:
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    _touch(project_dir / ".ce-config.json")

    existing_prd = project_dir / "prd" / "prd_structured.json"
    _touch(existing_prd)
    existing_prps = project_dir / "prps"
    existing_prps.mkdir(parents=True, exist_ok=True)
    _touch(existing_prps / "F0_plan.md")

    recorder = CommandRecorder()

    def init_cmd(**kwargs):
        recorder.record("init")

    def generate_prd_cmd(**kwargs):
        recorder.record("generate_prd")

    def generate_prps_cmd(**kwargs):
        recorder.record("generate_prps")

    def generate_tasks_cmd(**kwargs):
        recorder.record("generate_tasks")
        output = Path(kwargs["output"])
        output.mkdir(parents=True, exist_ok=True)
        _touch(output / "TASK.010.md")

    def validate_cmd(**kwargs):
        recorder.record("validate")

    service = AutopilotService()
    result = service.run_flow(
        invoker=_fake_invoker,
        echo=lambda msg: None,
        project_path=project_dir,
        project_name=None,
        stack="python-fastapi",
        idea_file=None,
        prd_file=str(existing_prd),
        prps_dir=str(existing_prps),
        tasks_dir=None,
        skip_validate=True,
        tasks_from_us=True,
        enable_ai=None,
        embedding_model=None,
        init_command=init_cmd,
        generate_prd_command=generate_prd_cmd,
        generate_prps_command=generate_prps_cmd,
        generate_tasks_command=generate_tasks_cmd,
        validate_command=validate_cmd,
    )

    assert recorder.calls == ["generate_tasks"]
    assert result["prd_path"] == existing_prd.resolve()
    assert Path(result["tasks_path"] or "").exists()


def test_run_flow_requires_input(tmp_path: Path) -> None:
    service = AutopilotService()
    with pytest.raises(click.ClickException):
        service.run_flow(
            invoker=_fake_invoker,
            echo=lambda msg: None,
            project_path=tmp_path,
            project_name=None,
            stack="python-fastapi",
            idea_file=None,
            prd_file=None,
            prps_dir=None,
            tasks_dir=None,
            skip_validate=False,
            tasks_from_us=False,
            enable_ai=None,
            embedding_model=None,
            init_command=lambda **_: None,
            generate_prd_command=lambda **_: None,
            generate_prps_command=lambda **_: None,
            generate_tasks_command=lambda **_: None,
            validate_command=lambda **_: None,
        )
