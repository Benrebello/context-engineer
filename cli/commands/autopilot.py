"""Autopilot workflow command for Context Engineer CLI."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from pathlib import Path

import click

from cli.shared import AUTOPILOT_SERVICE, embedding_model_option, hybrid_ai_option

CommandFactory = Callable[[], Callable]


def _resolve_cli_command(name: str) -> Callable:
    """Retrieve the latest command implementation from cli.main.

    This indirection preserves compatibility with legacy tests that monkeypatch
    cli.main.<command>, ensuring Autopilot sees the override.
    """
    cli_main = import_module("cli.main")
    return getattr(cli_main, name)


@click.command(
    help="Run the Autopilot (idea/PRD/PRPs/Tasks) without interaction, adapting to available inputs."
)
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(file_okay=False),
    help="Project directory (will be created when missing).",
)
@click.option("--project-name", help="Project name (defaults to folder name).")
@click.option("--stack", default="python-fastapi", help="Stack to apply during init when needed.")
@click.option(
    "--idea-file",
    type=click.Path(exists=True, dir_okay=False),
    help="Idea/PRD seed file (optional). When provided, PRD generation runs automatically.",
)
@click.option(
    "--prd-file",
    type=click.Path(exists=True, dir_okay=False),
    help="Existing structured PRD (optional). Use when prd_structured.json already exists.",
)
@click.option(
    "--prps-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Directory containing ready PRPs (optional).",
)
@click.option(
    "--tasks-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Directory with pre-generated Tasks (optional).",
)
@click.option("--skip-validate", is_flag=True, help="Skip final validation stage.")
@click.option("--tasks-from-us", is_flag=True, help="Create tasks from an interactive User Story.")
@hybrid_ai_option()
@embedding_model_option()
def autopilot(
    project_dir,
    project_name,
    stack,
    idea_file,
    prd_file,
    prps_dir,
    tasks_dir,
    skip_validate,
    tasks_from_us,
    enable_ai,
    embedding_model,
):
    """Execute the entire Context Engineer pipeline flexibly."""
    ctx = click.get_current_context()
    project_path = Path(project_dir).resolve()
    project_path.mkdir(parents=True, exist_ok=True)

    # Resolve commands from the entrypoint so monkeypatches remain visible.
    init = _resolve_cli_command("init")
    generate_prd = _resolve_cli_command("generate_prd")
    generate_prps = _resolve_cli_command("generate_prps")
    generate_tasks = _resolve_cli_command("generate_tasks")
    validate = _resolve_cli_command("validate")

    try:
        AUTOPILOT_SERVICE.run_flow(
            invoker=ctx.invoke,
            echo=click.echo,
            project_path=project_path,
            project_name=project_name,
            stack=stack,
            idea_file=idea_file,
            prd_file=prd_file,
            prps_dir=prps_dir,
            tasks_dir=tasks_dir,
            skip_validate=skip_validate,
            tasks_from_us=tasks_from_us,
            enable_ai=enable_ai,
            embedding_model=embedding_model,
            init_command=init,
            generate_prd_command=generate_prd,
            generate_prps_command=generate_prps,
            generate_tasks_command=generate_tasks,
            validate_command=validate,
        )
    except click.Abort:
        click.echo("\n[Autopilot] Execution interrupted.")
        raise
    except click.ClickException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        click.echo(f"\n[Autopilot] Failure during execution: {exc}", err=True)
        raise click.Abort()


__all__ = ["autopilot"]
