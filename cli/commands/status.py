"""Project status visualization and assistant commands."""

from __future__ import annotations

import webbrowser
from pathlib import Path

import click

from cli.shared import STATUS_SERVICE, embedding_model_option, hybrid_ai_option
from core.project_analyzer import ProjectAnalyzer

from .generation import generate_prd, generate_prps, generate_tasks, init, validate


@click.command(help="Display project status with progress and metrics.")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project directory.",
)
@click.option("--json", is_flag=True, help="Output in JSON format.")
@hybrid_ai_option()
@embedding_model_option()
def status(project_dir, json, enable_ai, embedding_model):
    """Show detailed status with suggestions."""
    try:
        project_path = Path(project_dir).resolve()
        data = STATUS_SERVICE.gather_status_data(
            project_path,
            enable_ai=enable_ai,
            embedding_model=embedding_model,
            include_suggestions=True,
        )

        if json:
            import json as json_lib

            click.echo(
                json_lib.dumps(
                    {"state": data["state"], "metrics": data["metrics"]},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return

        click.echo("\n" + STATUS_SERVICE.format_status_text(data))
    except Exception as exc:  # pragma: no cover - defensive
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


@click.command(help="Display an interactive project checklist.")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project directory.",
)
def checklist(project_dir):
    """Print a summarized checklist of phases."""
    try:
        project_path = Path(project_dir).resolve()
        data = STATUS_SERVICE.gather_status_data(
            project_path, include_suggestions=False, enable_ai=None, embedding_model=None
        )
        click.echo("\n" + STATUS_SERVICE.format_checklist_text(data["status_view"]))
    except Exception as exc:  # pragma: no cover
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


@click.command(help="Conversational assistant mode with guided steps.")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project directory.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "html"], case_sensitive=False),
    default="text",
    help="Assistant introduction format.",
)
@click.option(
    "--output-file",
    type=click.Path(dir_okay=False),
    help="Report destination when --format=html.",
)
@click.option(
    "--open",
    "open_report",
    is_flag=True,
    help="Open the HTML report in the browser (only when --format=html).",
)
@hybrid_ai_option()
@embedding_model_option()
def assist(project_dir, output_format, output_file, open_report, enable_ai, embedding_model):
    """Executa o assistente interativo com recomendações contextuais."""
    try:
        project_path = Path(project_dir).resolve()
        data = STATUS_SERVICE.run_assistant_flow(project_path, enable_ai=enable_ai, embedding_model=embedding_model)

        intro_context = {
            "assistant_context": data["assistant_context"],
            "pattern_suggestions": data["pattern_suggestions"],
            "cache_suggestions": data["cache_suggestions"],
            "metrics": data.get("metrics", {}),
            "status_view": data.get("status_view"),
        }
        normalized_format = (output_format or "text").lower()
        if open_report and normalized_format != "html":
            click.echo("[AVISO] --open é suportado apenas quando --format=html. Flag ignorada.")
            open_report = False
        if normalized_format == "html":
            intro = STATUS_SERVICE.render_assist_intro(intro_context, format="html")
            target_path = Path(output_file).resolve() if output_file else project_path / "assist_report.html"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(intro, encoding="utf-8")
            click.echo(f"\n[OK] Relatório HTML salvo em {target_path}")
            if open_report:
                try:
                    webbrowser.open(target_path.as_uri())
                except Exception as exc:  # pragma: no cover
                    click.echo(f"[AVISO] Não foi possível abrir o navegador automaticamente: {exc}")
        else:
            intro = STATUS_SERVICE.render_assist_intro(intro_context, format="text")
            click.echo("\n" + intro)

        ctx = click.get_current_context()

        def refresh_state() -> tuple[dict, dict]:
            analyzer = ProjectAnalyzer(project_path)
            refreshed_state = analyzer.analyze_project_state()
            return refreshed_state, refreshed_state["completion_status"]

        state = data["state"]
        completion = state["completion_status"]
        assistant_context = data["assistant_context"]
        project_name = assistant_context.get("project_name") or project_path.name
        stack_hint = assistant_context.get("stack")
        stack = stack_hint[0] if isinstance(stack_hint, list) and stack_hint else stack_hint or "python-fastapi"

        if not completion["init"]:
            click.echo("\nLet's start by initializing the project.")
            if click.confirm("Do you want to run 'ce init' now?", default=True):
                ctx.invoke(
                    init,
                    project_name=project_name,
                    template="base",
                    stack=stack,
                    output=str(project_path),
                    git_hooks=True,
                    enable_ai=enable_ai,
                    embedding_model=embedding_model,
                )
                click.echo("\n[OK] Project initialized successfully!")
                state, completion = refresh_state()

        if not completion["prd"]:
            click.echo("\nNext step: create the PRD (Product Requirements Document).")
            if click.confirm("Generate the PRD now?", default=True):
                ctx.invoke(
                    generate_prd,
                    input_file=None,
                    output=str(project_path / "prd"),
                    interactive=True,
                    enable_ai=enable_ai,
                    embedding_model=embedding_model,
                )
                click.echo("\n[OK] PRD created successfully!")
                state, completion = refresh_state()

        if not completion["prps"]:
            click.echo("\nNow, let's generate PRPs (Phase Requirement Plans).")
            if click.confirm("Generate PRPs now?", default=True):
                ctx.invoke(
                    generate_prps,
                    prd_file=None,
                    output=str(project_path / "prps"),
                    parallel=False,
                    interactive=True,
                    enable_ai=enable_ai,
                    embedding_model=embedding_model,
                )
                click.echo("\n[OK] PRPs generated successfully!")
                state, completion = refresh_state()

        if not completion["tasks"]:
            click.echo("\nTime to generate executable Tasks from the PRPs.")
            if click.confirm("Generate Tasks now?", default=True):
                ctx.invoke(
                    generate_tasks,
                    prps_dir=None,
                    output=str(project_path / "tasks"),
                    interactive=True,
                    from_us=False,
                    enable_ai=enable_ai,
                    embedding_model=embedding_model,
                )
                click.echo("\n[OK] Tasks generated successfully!")
                state, completion = refresh_state()

        click.echo("\n" + "=" * 70)
        click.echo("[OK] Guided process completed!")
        click.echo("=" * 70)
        click.echo("\nRecommended next steps:")
        click.echo("  • Review the generated files")
        click.echo("  • Run 'ce validate' to check traceability")
        click.echo("  • Run 'ce status' to inspect overall progress")
        click.echo("  • Start implementing Tasks via the IDE agents\n")

    except click.Abort:
        click.echo("\n\n[WARN] Assistant interrupted.")
    except Exception as exc:  # pragma: no cover
        click.echo(f"\n[ERROR] {exc}", err=True)
        raise click.Abort()


@click.command(help="Interactive wizard guiding you through the full Context Engineer flow.")
@click.option("--project-name", help="Project name.")
@click.option("--skip-init", is_flag=True, help="Skip project initialization step.")
@hybrid_ai_option()
@embedding_model_option()
def wizard(project_name, skip_init, enable_ai, embedding_model):
    """Step-by-step wizard reusing the main commands."""
    click.echo("\n" + "=" * 70)
    click.echo("🧙 CONTEXT ENGINEER WIZARD")
    click.echo("=" * 70)
    click.echo("\nThis wizard guides you through the full development pipeline.")
    click.echo("You can skip any step by pressing Ctrl+C and resume later.\n")

    try:
        ctx = click.get_current_context()
        if not skip_init:
            if click.confirm("\nStep 1: Initialize project?", default=True):
                if not project_name:
                    project_name = click.prompt("Project name", default=Path.cwd().name)

                stack = click.prompt(
                    "Tech stack",
                    type=click.Choice(
                        ["python-fastapi", "node-react", "vue3", "java-spring", "go-gin"],
                        case_sensitive=False,
                    ),
                    default="python-fastapi",
                )

                click.echo(f"\nInitializing project '{project_name}' with stack '{stack}'...")
                ctx.invoke(
                    init,
                    project_name=project_name,
                    template="base",
                    stack=stack,
                    output="./",
                    git_hooks=True,
                    enable_ai=enable_ai,
                    embedding_model=embedding_model,
                )

        if click.confirm("\nStep 2: Generate PRD?", default=True):
            choice = click.prompt("Choose (1=interactive, 2=file)", type=click.Choice(["1", "2"]), default="1")
            if choice == "1":
                ctx.invoke(
                    generate_prd,
                    input_file=None,
                    output="./prd",
                    interactive=True,
                    enable_ai=enable_ai,
                    embedding_model=embedding_model,
                )
            else:
                prd_file = click.prompt("PRD file path", type=click.Path(exists=True))
                ctx.invoke(
                    generate_prd,
                    input_file=prd_file,
                    output="./prd",
                    interactive=False,
                    enable_ai=enable_ai,
                    embedding_model=embedding_model,
                )

        if click.confirm("\nStep 3: Generate PRPs from the PRD?", default=True):
            ctx.invoke(
                generate_prps,
                prd_file=None,
                output="./prps",
                parallel=False,
                interactive=True,
                enable_ai=enable_ai,
                embedding_model=embedding_model,
            )

        if click.confirm("\nStep 4: Generate Tasks?", default=True):
            choice = click.prompt("Choose (1=PRPs, 2=User Story)", type=click.Choice(["1", "2"]), default="1")
            if choice == "1":
                ctx.invoke(
                    generate_tasks,
                    prps_dir=None,
                    output="./tasks",
                    interactive=True,
                    from_us=False,
                    enable_ai=enable_ai,
                    embedding_model=embedding_model,
                )
            else:
                ctx.invoke(
                    generate_tasks,
                    prps_dir=None,
                    output="./tasks",
                    interactive=False,
                    from_us=True,
                    enable_ai=enable_ai,
                    embedding_model=embedding_model,
                )

        if click.confirm("\nStep 5: Validate PRPs and Tasks?", default=True):
            prps_dir = click.prompt("PRPs directory", default="./prps", type=click.Path(exists=True, file_okay=False))
            ctx.invoke(
                validate,
                prps_dir=prps_dir,
                prd_file=None,
                tasks_dir=None,
                api_spec=None,
                ui_tasks_dir=None,
                soft_check=False,
            )

        click.echo("\n" + "=" * 70)
        click.echo("[OK] WIZARD COMPLETED!")
        click.echo("=" * 70)
        click.echo("\nNext steps:")
        click.echo("  • Review generated files")
        click.echo("  • Execute tasks using the IDE agents")
        click.echo("  • Use 'ce validate' to ensure traceability")
        click.echo("  • Use 'ce report' to review project metrics\n")
    except click.Abort:
        click.echo("\n\n[WARN] Wizard interrupted. You can resume later.")
    except Exception as exc:  # pragma: no cover
        click.echo(f"\n[ERROR] {exc}", err=True)
        raise click.Abort()


__all__ = ["status", "checklist", "assist", "wizard"]
