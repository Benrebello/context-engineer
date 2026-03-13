"""CLI commands for session management (pause/resume)."""

from pathlib import Path

import click


@click.group(name="session", help="Manage work sessions (pause/resume).")
def session() -> None:
    """Session management commands."""
    pass


@session.command(name="pause", help="Pause current work session.")
@click.option("--project-dir", default=".", help="Project root directory.")
@click.option("--note", default="", help="Optional note about current state.")
def pause_session(project_dir: str, note: str) -> None:
    """Save current work context and pause."""
    import json
    from datetime import datetime

    project_path = Path(project_dir).resolve()
    session_file = project_path / ".ide-rules" / "SESSION.json"
    session_file.parent.mkdir(parents=True, exist_ok=True)

    # Load current state
    state_file = project_path / ".ide-rules" / "STATE.json"
    state_data = {}
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)

    session_data = {
        "paused_at": datetime.now().isoformat(),
        "note": note,
        "state_snapshot": state_data,
        "status": "paused",
    }

    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)

    click.secho("⏸️  Session paused.", fg="yellow", bold=True)
    if note:
        click.echo(f"   Note: {note}")
    click.echo(f"   Saved to: {session_file}")
    click.secho("   Resume with: ce session resume", fg="cyan")


@session.command(name="resume", help="Resume a paused work session.")
@click.option("--project-dir", default=".", help="Project root directory.")
def resume_session(project_dir: str) -> None:
    """Restore saved work context and resume."""
    import json
    from datetime import datetime

    project_path = Path(project_dir).resolve()
    session_file = project_path / ".ide-rules" / "SESSION.json"

    if not session_file.exists():
        click.secho("❌ No paused session found.", fg="red")
        return

    with open(session_file, "r", encoding="utf-8") as f:
        session_data = json.load(f)

    paused_at = session_data.get("paused_at", "unknown")
    note = session_data.get("note", "")
    state_snapshot = session_data.get("state_snapshot", {})

    click.secho("▶️  Resuming session...", fg="green", bold=True)
    click.echo(f"   Paused at: {paused_at}")
    if note:
        click.echo(f"   Note: {note}")

    # Restore state
    if state_snapshot:
        current_milestone = state_snapshot.get("current_milestone", "unknown")
        progress = state_snapshot.get("progress_percentage", 0)
        tasks = state_snapshot.get("tasks", {})
        total_tasks = len(tasks)
        completed = sum(1 for t in tasks.values() if t.get("status") == "completed")

        click.echo(f"\n   📊 State: {current_milestone} ({progress}% done)")
        click.echo(f"   📋 Tasks: {completed}/{total_tasks} completed")

        # Show in-progress tasks
        in_progress = [
            (tid, t) for tid, t in tasks.items() if t.get("status") == "in_progress"
        ]
        if in_progress:
            click.echo("\n   🔄 In-progress tasks:")
            for tid, task in in_progress:
                click.echo(f"      - {tid}: {task.get('name', 'unnamed')}")

    # Mark session as resumed
    session_data["status"] = "resumed"
    session_data["resumed_at"] = datetime.now().isoformat()
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)

    click.secho("\n✅ Session restored. Ready to continue!", fg="green")


@session.command(name="status", help="Show current session status.")
@click.option("--project-dir", default=".", help="Project root directory.")
def session_status(project_dir: str) -> None:
    """Display the current session state."""
    import json

    project_path = Path(project_dir).resolve()
    session_file = project_path / ".ide-rules" / "SESSION.json"

    if not session_file.exists():
        click.secho("ℹ️  No session data found. Start working and pause when needed.", fg="blue")
        return

    with open(session_file, "r", encoding="utf-8") as f:
        session_data = json.load(f)

    status = session_data.get("status", "unknown")
    icon = "⏸️" if status == "paused" else "▶️" if status == "resumed" else "❔"

    click.echo(f"\n{icon} Session Status: {status}")
    click.echo(f"   Paused at: {session_data.get('paused_at', 'N/A')}")
    if session_data.get("resumed_at"):
        click.echo(f"   Resumed at: {session_data.get('resumed_at')}")
    if session_data.get("note"):
        click.echo(f"   Note: {session_data.get('note')}")
