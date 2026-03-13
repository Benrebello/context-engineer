"""CLI command for project state management."""

import click
from pathlib import Path
from core.progress import ExecutionState

@click.group()
def state():
    """Gerenciar o estado de execução do projeto."""
    pass

@state.command()
@click.option("--project-dir", default=".", help="Diretório do projeto")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Formato de saída")
def status(project_dir, format):
    """Visualizar o progresso atual do projeto."""
    state_manager = ExecutionState(Path(project_dir))
    state_manager.load()
    
    if format == "json":
        import json
        click.echo(json.dumps(state_manager.data, indent=2))
        return

    click.secho(f"\n🚀 Projeto: {state_manager.data['project_name']}", fg="cyan", bold=True)
    click.echo(f"📊 Status: {state_manager.data['status']}")
    click.echo(f"📍 Milestone: {state_manager.data['current_milestone']}")
    
    # Progress bar simple implementation
    progress = state_manager.data['progress_percentage']
    bar_length = 20
    filled_length = int(bar_length * progress // 100)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)
    click.echo(f"📈 Progresso: [{bar}] {progress}%\n")
    
    tasks = state_manager.data.get("tasks", {})
    if tasks:
        click.secho("📋 Tarefas:", bold=True)
        for tid, tdata in tasks.items():
            status = tdata['status']
            if status == "completed":
                icon, color = "✅", "green"
            elif status == "in_progress":
                icon, color = "⏳", "yellow"
            elif status == "failed":
                icon, color = "❌", "red"
            else:
                icon, color = "⬜", "white"
            
            click.echo(f"  {icon} ", nl=False)
            click.secho(f"{tid}: {tdata['name']} ({status})", fg=color)
    else:
        click.echo("Nenhuma tarefa registrada.")
    
    click.echo(f"\n🕒 Última atualização: {state_manager.data['last_updated']}")

@state.command()
@click.argument("task_id")
@click.argument("status")
@click.option("--name", help="Nome da tarefa (opcional se já existir)")
@click.option("--project-dir", default=".", help="Diretório do projeto")
def update(task_id, status, name, project_dir):
    """Atualizar o status de uma tarefa."""
    state_manager = ExecutionState(Path(project_dir))
    state_manager.load()
    
    # If name not provided, try to keep existing name
    if not name:
        existing_task = state_manager.data.get("tasks", {}).get(task_id)
        name = existing_task.get("name") if existing_task else task_id

    state_manager.update_task(task_id, name, status)
    color = "green" if status == "completed" else "yellow" if status == "in_progress" else "white"
    click.secho(f"✨ Tarefa {task_id} atualizada para {status}.", fg=color)

@state.command()
@click.argument("milestone")
@click.option("--project-dir", default=".", help="Diretório do projeto")
def milestone(milestone, project_dir):
    """Definir o milestone atual."""
    state_manager = ExecutionState(Path(project_dir))
    state_manager.set_milestone(milestone)
    click.secho(f"Milestone definido como: {milestone}", fg="green")
