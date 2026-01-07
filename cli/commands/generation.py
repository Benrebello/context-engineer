"""Artifact generation and validation commands for Context Engineer CLI."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import click

from cli.shared import (
    PROMPT_SERVICE,
    _generate_git_hooks,
    check_intelligence_mode,
    create_engine,
    echo_error,
    echo_info,
    echo_step,
    echo_success,
    echo_warning,
    embedding_model_option,
    get_project_language,
    hybrid_ai_option,
    normalize_embedding_model,
    save_project_config,
    validate_command_prerequisites,
)
from core.i18n import get_i18n
from core.metrics import MetricsCollector
from core.planning import EffortEstimator
from core.validators import PRPValidator

# ---------------------------------------------------------------------------
# Interactive helpers
# ---------------------------------------------------------------------------


@click.command(help="Initialize a Context Engineer project with scaffold, templates, and Git hooks.")
@click.argument("project_name", required=False, metavar="[PROJECT_NAME]")
@click.option("--template", default="base", help="Template to apply.")
@click.option("--stack", default="python-fastapi", help="Technology stack to scaffold.")
@click.option("--output", default="./", type=click.Path(), help="Output directory for generated assets.")
@click.option("--git-hooks", is_flag=True, default=True, help="Generate Git hooks for automatic validation.")
@click.option(
    "--language",
    "--lang",
    type=click.Choice(["en-us", "pt-br", "en", "pt"], case_sensitive=False),
    help="Project language for CLI messages (en-us or pt-br). Default: en-us",
)
@hybrid_ai_option("Choose which intelligence mode should assist during project creation.")
@embedding_model_option("Choose the embedding model for the newly created project.")
def init(
    project_name: str | None,
    template: str,
    stack: str,
    output: str,
    git_hooks: bool,
    language: str | None,
    enable_ai: bool | None,
    embedding_model: str | None,
) -> None:
    """Initialize a new Context Engineer project."""
    try:
        use_transformers = check_intelligence_mode(enable_override=enable_ai)
        output_path = Path(output).resolve()

        if not project_name:
            if output == "./" or str(output_path) == str(Path.cwd()):
                project_name = Path.cwd().name
            else:
                project_name = output_path.name

        engine = create_engine(use_transformers=use_transformers, embedding_model=embedding_model)
        result = engine.init_project(
            template=template, project_name=project_name, stack=stack, output_dir=output_path
        )

        # Determine language
        if not language:
            language = click.prompt(
                "Choose project language / Escolha o idioma do projeto",
                type=click.Choice(["en-us", "pt-br"], case_sensitive=False),
                default="en-us",
                show_default=True,
            )
        
        config_overrides = {
            "use_transformers": use_transformers,
            "language": language.lower(),
        }
        if embedding_model:
            config_overrides["embedding_model"] = normalize_embedding_model(embedding_model)
        save_project_config(output_path, config_overrides)
        
        # Get i18n instance with selected language
        i18n = get_i18n(language=language, project_dir=output_path)

        echo_success(i18n.t("cmd.init.success", name=project_name, path=output))
        echo_info(i18n.t("cmd.init.stack", stack=stack))

        created_dirs = result.get("created_directories", [])
        if created_dirs:
            click.echo(f"\nFolder structure created ({len(created_dirs)} directories):")
            for dir_path in sorted(created_dirs)[:10]:
                click.echo(f"   • {dir_path}/")
            if len(created_dirs) > 10:
                click.echo(f"   ... plus {len(created_dirs) - 10} more directories")
        
        echo_info(i18n.t("cmd.init.tip_alias"))

        created_files = result.get("created_files", [])
        if created_files:
            click.echo(f"\nBase files created ({len(created_files)} files):")
            for file_path in created_files:
                click.echo(f"   • {Path(file_path).name}")

        prp_files = result.get("generated_files", [])
        if prp_files:
            click.echo(f"\nPRP files generated ({len(prp_files)} files):")
            for prp_file in prp_files[:5]:
                click.echo(f"   • {Path(prp_file).name}")
            if len(prp_files) > 5:
                click.echo(f"   ... plus {len(prp_files) - 5} more files")

        try:
            subprocess.run(["prism", "--version"], capture_output=True, timeout=2, check=True)
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
            PermissionError,
            OSError,
        ):
            pass

        if git_hooks:
            git_dir = output_path / ".git"
            if git_dir.exists():
                _generate_git_hooks(output_path, project_name, soft_gate=True)
                click.echo(f"Git hooks provisioned at {git_dir / 'hooks'}")
            else:
                echo_warning(i18n.t("cmd.init.git_not_found"))
                echo_info(i18n.t("cmd.init.git_tip"))
                echo_info(i18n.t("cmd.init.git_later"))
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


def prompt_multiline(prompt_text: str, default: str = "") -> str:
    """Proxy para PromptService (mantido por compatibilidade)."""
    return PROMPT_SERVICE.prompt_multiline(prompt_text, default)


def prompt_user_story() -> dict:
    """Proxy para PromptService."""
    return PROMPT_SERVICE.prompt_user_story()


def prompt_prd_idea() -> dict:
    """Proxy para PromptService."""
    return PROMPT_SERVICE.prompt_prd_idea()


def prompt_prp_info() -> dict:
    """Proxy para PromptService."""
    return PROMPT_SERVICE.prompt_prp_info()


def save_interactive_input(content: str, filename: str, output_dir: Path) -> Path:
    """Save interactive input to a temporary file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename
    file_path.write_text(content, encoding="utf-8")
    return file_path


# ---------------------------------------------------------------------------
# Commands: generation pipeline
# ---------------------------------------------------------------------------


@click.command(help="Generate a PRD from an idea (interactive mode or file input).")
@click.argument("input_file", required=False, type=click.Path(exists=True))
@click.option("--output", default="./prd", type=click.Path(), help="Output directory for generated files.")
@click.option("--interactive", "-i", is_flag=True, help="Interactive conversational mode.")
@click.option("--auto-validate", is_flag=True, default=True, help="Auto-validate once generation completes.")
@click.option("--preview", is_flag=True, help="Show a preview without creating files.")
@hybrid_ai_option()
@embedding_model_option()
def generate_prd(
    input_file: str | None,
    output: str,
    interactive: bool,
    auto_validate: bool,
    preview: bool,
    enable_ai: bool | None,
    embedding_model: str | None,
) -> None:
    """Generate a PRD from the provided idea."""
    try:
        engine = create_engine(use_transformers=enable_ai, embedding_model=embedding_model)
        output_path = Path(output)

        if interactive or not input_file:
            click.echo("\nInteractive Mode: PRD generation")
            prd_data = prompt_prd_idea()
            prd_content = f"""# PRD - Product Requirements Document

## Product Vision
{prd_data['visao']}

## Market Context
{prd_data['contexto']}

## Target Users
{prd_data['usuarios']}

## Technical Constraints
{prd_data['restricoes']}

## Functional Requirements

"""
            for i, req in enumerate(prd_data["requisitos_funcionais"], 1):
                prd_content += f"{i}. {req}\n"

            temp_file = save_interactive_input(prd_content, "prd_input.md", output_path)
            input_file = temp_file

        if preview:
            click.echo("\nPreview: Files that will be generated")
            click.echo("─" * 70)
            click.echo(f"   {output_path / 'PRD.md'}")
            click.echo(f"   {output_path / 'prd_structured.json'}")
            click.echo("\nRun without --preview to actually generate the files.")
            return

        engine.generate_prd(input_file=Path(input_file), output_dir=output_path)
        echo_success(f"PRD generated at {output}")
        click.echo("   - PRD.md")
        click.echo("   - prd_structured.json")
        echo_info("Próximo passo: Execute 'ce generate-prps' ou 'ce gpr'")

        if auto_validate:
            click.echo("\nValidating PRD...")
            prd_file = output_path / "prd_structured.json"
            if prd_file.exists():
                try:
                    with open(prd_file, encoding="utf-8") as f:
                        prd_data = json.load(f)
                    required_fields = ["visao", "usuarios", "requisitos_funcionais"]
                    missing = [f for f in required_fields if f not in prd_data or not prd_data[f]]
                    if missing:
                        echo_warning(f"Missing fields: {', '.join(missing)}")
                    else:
                        echo_success("PRD validated successfully")
                except FileNotFoundError as exc:
                    i18n = get_i18n(project_dir=output_path)
                    echo_error(i18n.t("error.file_not_found", file=str(exc)))
                    echo_info(i18n.t("error.file_not_found_tip"))
                    raise click.Abort()
                except Exception as exc:
                    i18n = get_i18n(project_dir=output_path)
                    echo_error(i18n.t("error.unexpected", error=str(exc)))
                    echo_info(i18n.t("error.unexpected_tip"))
                    raise click.Abort()
    except FileNotFoundError as exc:
        i18n = get_i18n(project_dir=output_path)
        echo_error(i18n.t("error.file_not_found", file=str(exc)))
        echo_info(i18n.t("error.file_not_found_tip"))
        raise click.Abort()
    except PermissionError as exc:
        i18n = get_i18n(project_dir=output_path)
        echo_error(i18n.t("error.permission_denied", file=str(exc)))
        echo_info(i18n.t("error.permission_denied_tip"))
        raise click.Abort()
    except Exception as exc:
        i18n = get_i18n(project_dir=output_path)
        echo_error(i18n.t("error.unexpected", error=str(exc)))
        echo_info(i18n.t("error.unexpected_tip"))
        raise click.Abort()


@click.command(
    help="Generate PRPs (Phase Requirement Plans) for each phase (F1-F11) from an existing PRD."
)
@click.argument("prd_file", required=False, type=click.Path(exists=True))
@click.option("--output", default="./prps", type=click.Path(), help="Output directory for generated PRPs.")
@click.option("--parallel", is_flag=True, help="Generate phases in parallel.")
@click.option("--interactive", "-i", is_flag=True, help="Interactive conversational mode.")
@click.option("--auto-validate", is_flag=True, default=True, help="Auto-validate after generation.")
@click.option("--preview", is_flag=True, help="Show the list of files that would be created.")
@click.option("--phase", help="Generate only a specific phase (e.g., F3).")
@hybrid_ai_option()
@embedding_model_option()
def generate_prps(
    prd_file,
    output,
    parallel,
    interactive,
    auto_validate,
    preview,
    phase,
    enable_ai,
    embedding_model,
):
    """Generate PRPs from a PRD."""
    try:
        # Validate prerequisites
        if not validate_command_prerequisites("generate-prps", Path.cwd()):
            raise click.Abort()
        
        engine = create_engine(use_transformers=enable_ai, embedding_model=embedding_model)
        output_path = Path(output)

        if interactive or not prd_file:
            possible_prd_files = [
                Path("./prd/prd_structured.json"),
                Path("./prd_structured.json"),
                Path("./PRD.md"),
            ]

            found_prd = None
            for prd_path in possible_prd_files:
                if prd_path.exists():
                    found_prd = prd_path
                    click.echo(f"\nPRD detected at: {found_prd}")
                    break

            if not found_prd:
                if interactive:
                    echo_warning("PRD not found automatically.")
                    prd_file_path = click.prompt(
                        "Type the path to the PRD file", type=click.Path(exists=True)
                    )
                    found_prd = Path(prd_file_path)
                else:
                    echo_error("PRD not found. Use --interactive for guided mode or pass the PRD file path.")
                    echo_info("Execute 'ce generate-prd' primeiro ou use 'ce gpr --interactive'")
                    raise click.Abort()

            prd_file = found_prd
            prp_info = prompt_prp_info()
            click.echo(f"\nUsing prioritization method: {prp_info['metodo_priorizacao']}")
            if prp_info["contexto_adicional"]:
                click.echo("Additional context will be considered when generating PRPs.")

        if preview:
            click.echo("\nPreview: Phases that would be generated")
            click.echo("─" * 70)
            expected_phases = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11"]
            if phase:
                click.echo(f"   {output_path / f'{phase}_*.md'}")
            else:
                for ph in expected_phases:
                    click.echo(f"   {output_path / f'{ph}_*.md'}")
            click.echo("\nRun without --preview to generate the files.")
            return

        result = engine.generate_prps(
            prd_file=Path(prd_file), output_dir=output_path, parallel=parallel
        )
        click.echo(f"\n[OK] PRPs generated at {output}")
        for phase_file in result.get("phases", [])[:10]:
            click.echo(f"   - {Path(phase_file).name}")
        if len(result.get("phases", [])) > 10:
            click.echo(f"   ... plus {len(result.get('phases', [])) - 10} additional files")

        if auto_validate and not phase:
            click.echo("\nValidating PRPs...")
            try:
                ctx = click.get_current_context()
                ctx.invoke(
                    validate,
                    prps_dir=output_path,
                    prd_file=prd_file,
                    tasks_dir=None,
                    api_spec=None,
                    ui_tasks_dir=None,
                    soft_check=True,
                )
            except Exception:
                click.echo("   [WARN] Validation reported issues. Run 'ce validate' for full details.")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


@click.command(help="Generate executable TASKs from PRPs or User Stories.")
@click.argument("prps_dir", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("--output", default="./tasks", type=click.Path(), help="Output directory for generated TASKs.")
@click.option("--interactive", "-i", is_flag=True, help="Interactive conversational mode.")
@click.option("--from-us", is_flag=True, help="Generate TASKs from an interactive User Story.")
@hybrid_ai_option()
@embedding_model_option()
def generate_tasks(prps_dir, output, interactive, from_us, enable_ai, embedding_model):
    """Create executable TASKs from PRPs or direct User Stories."""
    try:
        engine = create_engine(use_transformers=enable_ai, embedding_model=embedding_model)
        output_path = Path(output)

        if from_us or (interactive and not prps_dir):
            click.echo("\nInteractive Mode: Generating a Task from a User Story")
            us_data = prompt_user_story()
            us_content = f"""# User Story: {us_data['title']}

## As {us_data['persona']}
## I want {us_data['acao']}
## So that {us_data['valor']}

## Acceptance Criteria

"""
            for criterio in us_data["criterios_aceitacao"]:
                us_content += f"- {criterio}\n"

            us_file = save_interactive_input(us_content, "user_story_input.md", output_path)
            click.echo(f"\n[OK] User Story saved at: {us_file}")
            click.echo("[TIP] Use the @Agente_Task_Direto.md agent inside the IDE for the full Task flow")
            click.echo("   or provide the PRPs directory via: ce generate-tasks ./prps")
            return

        if not prps_dir:
            possible_prp_dirs = [Path("./prps"), Path("./PRPs")]
            found_prps = None
            for prp_dir in possible_prp_dirs:
                if prp_dir.exists() and prp_dir.is_dir():
                    found_prps = prp_dir
                    click.echo(f"\nPRPs found at: {found_prps}")
                    break

            if not found_prps:
                if interactive:
                    click.echo("\n[WARN] PRPs directory not detected automatically.")
                    prps_dir_path = click.prompt(
                        "Provide the path to the PRPs directory",
                        type=click.Path(exists=True, file_okay=False),
                    )
                    found_prps = Path(prps_dir_path)
                else:
                    click.echo("\n[ERROR] PRPs directory not found.")
                    click.echo("   Use --interactive for guided mode or --from-us to generate from a User Story.")
                    raise click.Abort()

            prps_dir = found_prps

        result = engine.generate_tasks(prps_dir=Path(prps_dir), output_dir=output_path)
        click.echo(f"\n[OK] {len(result.get('tasks', []))} TASKs generated at {output}")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


@click.command(
    help="Validate PRPs with full traceability, dependency checks, and contract integrity (Deep Cross-Validation)."
)
@click.argument("prps_dir", type=click.Path(exists=True, file_okay=False))
@hybrid_ai_option()
@click.option("--prd-file", type=click.Path(exists=True), help="PRD file used for consistency validation.")
@click.option(
    "--tasks-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Directory with TASKs for traceability validation.",
)
@click.option("--api-spec", type=click.Path(exists=True), help="OpenAPI file for contract validation.")
@click.option(
    "--ui-tasks-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Directory containing UI tasks for contract validation.",
)
@click.option("--soft-check", is_flag=True, default=False, help="Advisory mode for Git hooks.")
@click.option("--dry-run", is_flag=True, help="Show what would be validated without running it.")
@click.option("--help-contextual", is_flag=True, help="Display contextual help about validation.")
@click.option(
    "--commits-json",
    type=click.Path(exists=True),
    help="JSON file mapping Task → commits/PRs for inverse validation.",
)
@click.option("--project-name", help="Project name for recording inverse traceability metrics.")
def validate(
    prps_dir,
    enable_ai,
    prd_file,
    tasks_dir,
    api_spec,
    ui_tasks_dir,
    soft_check,
    dry_run,
    help_contextual,
    commits_json,
    project_name,
):
    """Validate PRPs with complete traceability and contract integrity."""
    if help_contextual:
        click.echo("\n" + "=" * 70)
        click.echo("Contextual Help: validate")
        click.echo("=" * 70)
        click.echo(
            """
You are validating PRPs (Phase Requirement Plans).

What does validation include?
   • Traceability between PRPs and the PRD
   • Dependencies between phases
   • Cross-phase consistency
   • Contracts (API ↔ UI) when additional parameters are provided
"""
        )
        return

    try:
        if dry_run:
            click.echo("\nDry-Run: What would be validated")
            click.echo("─" * 70)
            click.echo(f"   PRPs: {prps_dir}")
            if prd_file:
                click.echo(f"   PRD: {prd_file}")
            if tasks_dir:
                click.echo(f"   Tasks: {tasks_dir}")
            if api_spec and ui_tasks_dir:
                click.echo("   Deep Cross-Validation:")
                click.echo(f"      • API Spec: {api_spec}")
                click.echo(f"      • UI Tasks: {ui_tasks_dir}")
            click.echo("\nRun without --dry-run to execute the full validation.")
            return

        validator = PRPValidator()
        prps_path = Path(prps_dir)
        prd_path = Path(prd_file) if prd_file else None
        tasks_path = Path(tasks_dir) if tasks_dir else None

        results = validator.validate_all(
            prps_path,
            prd_path,
            tasks_path,
        )

        if api_spec and ui_tasks_dir:
            click.echo("\nRunning Deep Cross-Validation (Contract Integrity)...")
            contract_result = validator.validate_contract_integrity(
                Path(api_spec), Path(ui_tasks_dir)
            )
            results["contract_integrity"] = contract_result.to_dict()

        all_valid = True
        error_count = 0
        warning_count = 0

        if commits_json:
            inverse_result = validator.validate_inverse_traceability(
                commits_mapping_path=Path(commits_json),
                tasks_dir=tasks_path,
                project_name=project_name,
            )
            results["inverse_traceability"] = inverse_result.to_dict()

            if project_name and inverse_result.get("statistics"):
                stats = inverse_result["statistics"]
                try:
                    metrics_collector = MetricsCollector(Path(".cache") / "metrics")
                    metrics_collector.record_traceability_status(
                        project_name,
                        tasks_with_commits=stats["tasks_with_commits"],
                        total_tasks=stats["total_tasks"],
                    )
                except Exception as metrics_error:
                    click.echo(f"[WARN] Could not save metrics: {metrics_error}")

        for name, result in results.items():
            if name in ["dependencies", "consistency", "traceability", "contract_integrity"]:
                if not result.get("valid", True):
                    all_valid = False
                    errors = result.get("errors", [])
                    warnings = result.get("warnings", [])
                    error_count += len(errors)
                    warning_count += len(warnings)

                    click.echo(f"\n{name.upper().replace('_', ' ')}: {len(errors)} error(s)")
                    click.echo(" " + "─" * 70)
                    for i, error in enumerate(errors, 1):
                        click.echo(f"  {i}. {error}")
                    if warnings:
                        click.echo(f"\n  Warnings ({len(warnings)}):")
                        for i, warning in enumerate(warnings, 1):
                            click.echo(f"    {i}. {warning}")
                else:
                    click.echo(f"{name.upper().replace('_', ' ')}: valid")
                    if result.get("warnings"):
                        warnings = result.get("warnings", [])
                        warning_count += len(warnings)
                        for warning in warnings:
                            click.echo(f"   {warning}")
            elif result.get("valid"):
                click.echo(f"{name}: valid")
            else:
                all_valid = False
                click.echo(f"{name}: {result.get('errors', [])}")

        if all_valid:
            click.echo("\nAll PRPs are valid")
        else:
            click.echo("\nSome PRPs contain errors")
            if not soft_check:
                raise click.Abort()
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


@click.command(help="Check dependencies between TASKs.")
@click.argument("tasks_dir", type=click.Path(exists=True, file_okay=False))
@hybrid_ai_option()
@embedding_model_option()
def check_dependencies(tasks_dir, enable_ai, embedding_model):
    """Verify dependency integrity between TASKs."""
    try:
        engine = create_engine(use_transformers=enable_ai, embedding_model=embedding_model)
        result = engine.check_dependencies(Path(tasks_dir))

        if result["valid"]:
            click.echo("All dependencies are valid.")
        else:
            click.echo("Issues detected:")
            for error in result.get("errors", []):
                click.echo(f" - {error}")
            raise click.Abort()
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


@click.command(help="Estimate effort (story points) for a single Task.")
@click.argument("task_file", type=click.Path(exists=True))
@click.option("--stack", default="python-fastapi", help="Technology stack.")
@click.option("--project-name", help="Project name for historical adjustments.")
@click.option("--detailed", is_flag=True, help="Show a detailed breakdown.")
def estimate_effort(task_file, stack, project_name, detailed):
    """Estimate story points for a specific Task."""
    try:
        with open(task_file, encoding="utf-8") as f:
            if task_file.endswith(".json"):
                task = json.load(f)
            else:
                content = f.read()
                match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
                if match:
                    task = json.loads(match.group(1))
                else:
                    click.echo("Could not extract JSON payload from the Task.", err=True)
                    raise click.Abort()

        metrics_collector = MetricsCollector(Path(".cache") / "metrics")
        estimator = EffortEstimator(metrics_collector)

        points = estimator.estimate_effort_points(task, stack, project_name)

        click.echo(f"Effort estimate: {points} story points")

        if detailed:
            breakdown = estimator.get_complexity_breakdown(task, stack)
            click.echo("\nComplexity Breakdown:")
            click.echo(f" • Artifacts: {breakdown['complexity_metrics']['artifacts']}")
            click.echo(f" • Steps: {breakdown['complexity_metrics']['steps']}")
            click.echo(f" • Test scenarios: {breakdown['complexity_metrics']['test_scenarios']}")
            click.echo(f" • Dependencies: {breakdown['complexity_metrics']['dependencies']}")
            click.echo(
                f" • Stack complexity: {breakdown['complexity_metrics']['stack_complexity']:.2f}"
            )
            click.echo(
                f" • Category complexity: {breakdown['complexity_metrics']['category_complexity']:.2f}"
            )

    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


@click.command(help="Estimate effort (story points) for multiple Tasks at once.")
@click.argument("tasks_dir", type=click.Path(exists=True, file_okay=False))
@click.option("--stack", default="python-fastapi", help="Technology stack.")
@click.option("--project-name", help="Project name for historical adjustments.")
@click.option("--output", type=click.Path(), help="Output JSON file.")
def estimate_batch(tasks_dir, stack, project_name, output):
    """Estimate story points for multiple Tasks simultaneously."""
    try:
        tasks_dir_path = Path(tasks_dir)
        task_files = list(tasks_dir_path.glob("TASK.*.json")) + list(tasks_dir_path.glob("TASK.*.md"))

        if not task_files:
            click.echo("No Tasks found.", err=True)
            raise click.Abort()

        metrics_collector = MetricsCollector(Path(".cache") / "metrics")
        estimator = EffortEstimator(metrics_collector)

        estimates = {}
        total_points = 0

        for task_file in task_files:
            try:
                with open(task_file, encoding="utf-8") as f:
                    if task_file.suffix == ".json":
                        task = json.load(f)
                    else:
                        content = f.read()
                        match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
                        if match:
                            task = json.loads(match.group(1))
                        else:
                            click.echo(f"Could not extract JSON payload from the Task {task_file.name}.", err=True)
                            continue

                task_id = task.get("task_id", task_file.stem)
                points = estimator.estimate_effort_points(task, stack, project_name)
                estimates[task_id] = points
                total_points += points
            except Exception as exc:
                click.echo(f"Error while processing {task_file.name}: {exc}")
                continue

        click.echo(f"Effort estimates ({len(estimates)} tasks):\n")
        for task_id, points in sorted(estimates.items()):
            click.echo(f" • {task_id}: {points} pts")

        click.echo(f"\nTotal: {total_points} story points")

        if output:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "estimates": estimates,
                        "total_points": total_points,
                        "stack": stack,
                        "project_name": project_name,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            click.echo(f"\nEstimates saved to {output}")

    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


__all__ = [
    "init",
    "generate_prd",
    "generate_prps",
    "generate_tasks",
    "validate",
    "check_dependencies",
    "estimate_effort",
    "estimate_batch",
    "prompt_multiline",
    "prompt_user_story",
    "prompt_prd_idea",
    "prompt_prp_info",
    "save_interactive_input",
]
