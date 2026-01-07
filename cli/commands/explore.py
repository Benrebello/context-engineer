"""Command explorer - helps users discover available commands by category."""

from __future__ import annotations

import click


@click.command(help="Explora comandos disponíveis organizados por categoria")
@click.option("--category", help="Filtrar por categoria específica")
def explore(category: str | None) -> None:
    """Show categorized command explorer to help users discover features."""
    categories = {
        "🎯 Geração": {
            "description": "Comandos para gerar artefatos do projeto",
            "commands": [
                ("init", "Inicializar projeto com estrutura e templates", "ce init my-project --stack python-fastapi"),
                ("generate-prd", "Gerar PRD a partir de uma ideia", "ce generate-prd --interactive"),
                ("generate-prps", "Gerar PRPs (fases) a partir do PRD", "ce generate-prps"),
                ("generate-tasks", "Gerar tasks executáveis", "ce generate-tasks"),
            ],
            "aliases": "Aliases: gp (generate-prd), gpr (generate-prps), gt (generate-tasks)",
        },
        "✅ Validação": {
            "description": "Comandos para validar qualidade e rastreabilidade",
            "commands": [
                ("validate", "Validar PRD, PRPs e Tasks", "ce validate --check-traceability"),
                ("doctor", "Diagnóstico completo do projeto", "ce doctor --fix"),
                ("checklist", "Checklist interativo de progresso", "ce checklist"),
                ("check-dependencies", "Verificar dependências do projeto", "ce check-dependencies"),
            ],
            "aliases": "Aliases: v (validate), c (checklist)",
        },
        "📊 Relatórios": {
            "description": "Comandos para visualizar métricas e status",
            "commands": [
                ("status", "Dashboard completo do projeto", "ce status --detailed"),
                ("report", "Relatório de eficiência", "ce report"),
                ("metrics-summary", "Resumo de métricas", "ce metrics-summary"),
                ("ai-status", "Status da governança de IA", "ce ai-status"),
            ],
            "aliases": "Aliases: s (status)",
        },
        "🤖 Automação": {
            "description": "Comandos para automação e assistência",
            "commands": [
                ("quickstart", "Guia rápido de 5 minutos", "ce quickstart"),
                ("autopilot", "Modo autopilot (end-to-end)", "ce autopilot --idea-file idea.txt"),
                ("wizard", "Wizard interativo passo a passo", "ce wizard"),
                ("assist", "Assistente conversacional", "ce assist --format html --open"),
            ],
            "aliases": "Aliases: auto (autopilot), a (assist)",
        },
        "🔧 DevOps": {
            "description": "Comandos para CI/CD e Git",
            "commands": [
                ("ci-bootstrap", "Gerar workflow GitHub Actions", "ce ci-bootstrap"),
                ("install-hooks", "Instalar Git hooks", "ce install-hooks"),
                ("generate-commit-map", "Mapear commits para tasks", "ce generate-commit-map"),
            ],
            "aliases": "Aliases: ci (ci-bootstrap)",
        },
        "🧩 Extensões": {
            "description": "Comandos para padrões e marketplace",
            "commands": [
                ("patterns", "Gerenciar biblioteca de padrões", "ce patterns list"),
                ("marketplace", "Explorar marketplace", "ce marketplace list"),
                ("ide", "Sincronizar prompts IDE", "ce ide sync"),
            ],
        },
        "⚙️ Configuração": {
            "description": "Comandos para configuração e governança",
            "commands": [
                ("ai-governance", "Gerenciar governança de IA", "ce ai-governance status"),
                ("alias", "Gerenciar aliases personalizados", "ce alias list"),
                ("estimate-effort", "Estimar esforço de tasks", "ce estimate-effort"),
            ],
        },
    }

    click.echo("\n" + "=" * 70)
    click.secho("🔍 EXPLORADOR DE COMANDOS - CONTEXT ENGINEER", fg="cyan", bold=True)
    click.echo("=" * 70)

    if category:
        # Filter by specific category
        category_key = None
        for key in categories:
            if category.lower() in key.lower():
                category_key = key
                break

        if not category_key:
            click.secho(f"\n✗ Categoria '{category}' não encontrada", fg="red")
            click.echo("\nCategorias disponíveis:")
            for cat_name in categories:
                click.echo(f"  • {cat_name}")
            return

        _display_category(category_key, categories[category_key])
    else:
        # Show all categories
        for cat_name, cat_data in categories.items():
            _display_category(cat_name, cat_data)
            click.echo("")

    click.echo("=" * 70)
    click.echo("\n💡 Dicas:")
    click.echo("  • Use 'ce <comando> --help' para ver detalhes de cada comando")
    click.echo("  • Use 'ce explore --category geração' para filtrar por categoria")
    click.echo("  • Execute 'ce quickstart' para começar rapidamente")
    click.echo("")


def _display_category(name: str, data: dict) -> None:
    """Display a single category with its commands."""
    click.echo(f"\n{name}")
    click.secho(f"{data['description']}", fg="white", dim=True)
    click.echo("─" * 70)

    for cmd_name, cmd_desc, cmd_example in data["commands"]:
        click.secho(f"  {cmd_name}", fg="green", bold=True)
        click.echo(f"    {cmd_desc}")
        click.secho(f"    Exemplo: {cmd_example}", fg="yellow", dim=True)
        click.echo("")

    if "aliases" in data:
        click.secho(f"  {data['aliases']}", fg="blue", dim=True)


__all__ = ["explore"]
