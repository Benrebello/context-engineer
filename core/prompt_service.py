"""Interactive prompt helpers extracted from the CLI."""

from __future__ import annotations

from pathlib import Path

import click

from core.i18n import get_i18n


class PromptService:
    """Wraps interactive prompts used by the CLI commands."""

    def prompt_multiline(self, prompt_text: str, default: str = "", project_dir: Path | None = None) -> str:
        i18n = get_i18n(project_dir=project_dir)
        
        click.echo(f"\n{prompt_text}")
        click.echo("")
        click.secho(i18n.t("prompt.multiline_title"), fg="yellow", bold=True)
        click.secho(f"  • {i18n.t('prompt.multiline_enter')}", fg="yellow")
        click.secho(f"  • {i18n.t('prompt.multiline_ctrl_d')}", fg="yellow")
        click.echo("─" * 70)

        lines: list[str] = []
        if default:
            click.echo(f"[Padrão: {default[:50]}...]")

        try:
            while True:
                try:
                    line = input()
                    if not line and not lines:
                        if default:
                            return default
                        continue
                    if not line and lines:
                        break
                    lines.append(line)
                except EOFError:
                    break
        except KeyboardInterrupt:
            click.echo("\n\nEntrada cancelada.")
            raise click.Abort() from None

        result = "\n".join(lines)
        return result if result.strip() else default

    def prompt_user_story(self) -> dict:
        click.echo("\n" + "=" * 70)
        click.echo("ENTRADA DE USER STORY")
        click.echo("=" * 70)

        persona = click.prompt("\nComo [persona]", default="usuário")
        acao = click.prompt("Eu quero [ação]", default="")
        valor = click.prompt("Para que [valor de negócio]", default="")

        click.echo("\nCritérios de Aceitação (formato Gherkin)")
        click.echo("Exemplo:")
        click.echo("  Dado que estou logado")
        click.echo("  Quando acesso a página de perfil")
        click.echo("  Então vejo minhas informações")

        criterios_text = self.prompt_multiline("\nDigite os critérios de aceitação (uma linha por critério):")
        criterios = [c.strip() for c in criterios_text.split("\n") if c.strip()]

        return {
            "persona": persona,
            "acao": acao,
            "valor": valor,
            "criterios_aceitacao": criterios,
            "title": f"{acao} - {valor[:50]}",
        }

    def prompt_prd_idea(self) -> dict:
        click.echo("\n" + "=" * 70)
        click.echo("ENTRADA DE IDEIA PARA PRD")
        click.echo("=" * 70)

        visao = self.prompt_multiline("\nVisão do Produto", "Aplicativo web para gestão de tarefas")
        contexto = self.prompt_multiline(
            "\nContexto de Mercado",
            "Mercado de produtividade, concorrência com ferramentas existentes",
        )
        usuarios = self.prompt_multiline(
            "\nUsuários-Alvo",
            "Gerentes de projeto, desenvolvedores, designers",
        )
        restricoes = self.prompt_multiline("\nRestrições Técnicas", "LGPD compliance, performance < 200ms")

        click.echo("\nRequisitos Funcionais")
        click.echo("(Digite um requisito por linha. Pressione Enter duas vezes para finalizar)")
        requisitos_text = self.prompt_multiline("")
        requisitos = [r.strip() for r in requisitos_text.split("\n") if r.strip()]

        return {
            "visao": visao,
            "contexto": contexto,
            "usuarios": usuarios,
            "restricoes": restricoes,
            "requisitos_funcionais": requisitos,
        }

    def prompt_prp_info(self) -> dict:
        click.echo("\n" + "=" * 70)
        click.echo("INFORMAÇÕES PARA GERAÇÃO DE PRPs")
        click.echo("=" * 70)

        fornecer_contexto = click.confirm("")
        contexto_adicional = ""
        if fornecer_contexto:
            contexto_adicional = self.prompt_multiline(
                "\nDigite o contexto adicional (arquitetura preferida, padrões, etc.):"
            )

        metodo_priorizacao = click.prompt(
            "\nMétodo de Priorização",
            type=click.Choice(["MoSCoW", "RICE", "Value-Effort"], case_sensitive=False),
            default="MoSCoW",
        )

        return {
            "contexto_adicional": contexto_adicional,
            "metodo_priorizacao": metodo_priorizacao,
        }
