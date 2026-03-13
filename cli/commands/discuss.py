"""CLI commands for the discuss/context capture phase."""

from pathlib import Path

import click


@click.command(name="discuss", help="Capture context and decisions for a phase.")
@click.argument("phase_id")
@click.option("--project-dir", default=".", help="Project root directory.")
@click.option("--batch", is_flag=True, default=False, help="Show all questions at once.")
def discuss(phase_id: str, project_dir: str, batch: bool) -> None:
    """Identify gray areas and capture user preferences for a phase."""
    from core.context_capture import ContextCapture

    project_path = Path(project_dir).resolve()
    capture = ContextCapture(project_path)

    # Try to load PRP data
    prp_data = _load_phase_prp(project_path, phase_id)
    if not prp_data:
        click.secho(f"⚠️  No PRP data found for phase {phase_id}.", fg="yellow")
        prp_data = {"title": f"Phase {phase_id}"}

    questions = capture.analyze_phase(phase_id, prp_data)

    if not questions:
        click.secho("✅ No gray areas detected for this phase.", fg="green")
        context_path = capture.generate_context(phase_id, prp_data)
        click.echo(f"   Context saved to: {context_path}")
        return

    click.secho(f"\n🔍 Gray areas detected for Phase {phase_id}:\n", fg="cyan", bold=True)

    answers: dict[str, str] = {}

    if batch:
        # Show all questions grouped by category
        for category, category_questions in questions.items():
            click.secho(f"  [{category.upper()}]", fg="yellow", bold=True)
            for q in category_questions:
                click.echo(f"    • {q}")
            click.echo("")

        click.secho("Answer each question (press Enter to skip):\n", fg="cyan")
        for category, category_questions in questions.items():
            for q in category_questions:
                answer = click.prompt(f"  {q}", default="", show_default=False)
                if answer:
                    answers[q] = answer
    else:
        # One-by-one interactive mode
        total_questions: int = sum(len(qs) for qs in questions.values())
        current: int = 0

        for category, category_questions in questions.items():
            click.secho(f"\n📂 {category.title()} Questions:\n", fg="yellow", bold=True)
            for q in category_questions:
                current = current + 1
                click.echo(f"  [{current}/{total_questions}] {q}")
                answer = click.prompt("  Your decision", default="skip", show_default=True)
                if answer != "skip":
                    answers[q] = answer

    # Generate context file
    context_path = capture.generate_context(phase_id, prp_data, answers)
    click.secho(f"\n✅ Context captured: {context_path}", fg="green")
    click.echo(f"   {len(answers)} decision(s) recorded.")


def _load_phase_prp(project_path: Path, phase_id: str) -> dict | None:
    """Try to load PRP data for a given phase."""
    import json

    prp_patterns = [
        project_path / "PRPs" / f"PRP-{phase_id}.json",
        project_path / "PRPs" / f"phase-{phase_id}.json",
    ]
    for pattern in prp_patterns:
        if pattern.exists():
            with open(pattern, "r", encoding="utf-8") as f:
                return json.load(f)
    return None
