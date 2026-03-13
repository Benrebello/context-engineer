"""CLI commands for verification and UAT."""

from pathlib import Path

import click


@click.command(name="verify", help="Run verification for a specific phase.")
@click.argument("phase_id")
@click.option("--project-dir", default=".", help="Project root directory.")
def verify_phase(phase_id: str, project_dir: str) -> None:
    """Generate and display UAT checklist for a phase."""
    from core.verification import VerificationEngine

    project_path = Path(project_dir).resolve()
    engine = VerificationEngine(project_path)

    # Try to load PRP data for the phase
    prp_data = _load_phase_prp(project_path, phase_id)
    if not prp_data:
        click.secho(f"⚠️  No PRP data found for phase {phase_id}. Generating empty UAT.", fg="yellow")
        prp_data = {"title": f"Phase {phase_id}"}

    uat_path = engine.generate_uat(phase_id, prp_data)
    click.secho(f"✅ UAT generated: {uat_path}", fg="green")

    # Display deliverables
    deliverables = engine.extract_deliverables(phase_id, prp_data)
    if deliverables:
        click.echo(f"\n📋 {len(deliverables)} deliverables to verify:")
        for i, d in enumerate(deliverables, 1):
            click.echo(f"  {i}. {d['name']}: {d['criterion']}")
    else:
        click.secho("  No testable deliverables found.", fg="yellow")


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
