"""Service responsible for orchestrating the Autopilot CLI workflow."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Union

import click

CommandCallable = Callable[..., Any]
InvokerCallable = Callable[..., Any]
EchoCallable = Callable[[str], None]
PathLike = Union[str, Path]


class AutopilotService:
    """Coordinates the Context Engineer Autopilot pipeline independent of CLI concerns."""

    def __init__(self, config_filename: str = ".ce-config.json") -> None:
        self.config_filename = config_filename

    @staticmethod
    def _resolve_path(candidate: PathLike | None) -> Path | None:
        """Return a resolved path when a candidate is provided."""
        if not candidate:
            return None
        return Path(candidate).resolve()

    @staticmethod
    def _invoke(invoker: InvokerCallable, command: CommandCallable, **kwargs: Any) -> None:
        """Invoke a Click command or plain callable in a unified way."""
        if hasattr(command, "__click_params__") or isinstance(command, click.Command):
            invoker(command, **kwargs)
            return
        command(**kwargs)

    def run_flow(
        self,
        *,
        invoker: InvokerCallable,
        echo: EchoCallable,
        project_path: Path,
        project_name: str | None,
        stack: str,
        idea_file: PathLike | None,
        prd_file: PathLike | None,
        prps_dir: PathLike | None,
        tasks_dir: PathLike | None,
        skip_validate: bool,
        tasks_from_us: bool,
        enable_ai: bool | None,
        embedding_model: str | None,
        init_command: CommandCallable,
        generate_prd_command: CommandCallable,
        generate_prps_command: CommandCallable,
        generate_tasks_command: CommandCallable,
        validate_command: CommandCallable,
    ) -> dict[str, Path | None]:
        """Execute Autopilot, generating missing artifacts and running validation when required."""
        if not any([idea_file, prd_file, prps_dir, tasks_dir, tasks_from_us]):
            raise click.ClickException(
                "Forneça ao menos uma entrada (--idea-file, --prd-file, --prps-dir, --tasks-dir ou --tasks-from-us)."
            )

        echo("\n[Autopilot] Iniciando pipeline flexível...")
        inferred_name = project_name or project_path.name
        config_path = project_path / self.config_filename

        current_prd_path = self._resolve_path(prd_file)
        current_prps_path = self._resolve_path(prps_dir)
        current_tasks_path = self._resolve_path(tasks_dir)

        if not config_path.exists():
            echo("[Autopilot] Projeto ainda não inicializado. Executando ce init...")
            self._invoke(
                invoker,
                init_command,
                project_name=inferred_name,
                template="base",
                stack=stack,
                output=str(project_path),
                git_hooks=True,
                enable_ai=enable_ai,
                embedding_model=embedding_model,
            )

        if idea_file:
            idea_path = Path(idea_file).resolve()
            echo("\n[Autopilot] Gerando PRD a partir da ideia fornecida...")
            prd_output = project_path / "prd"
            prd_output.mkdir(parents=True, exist_ok=True)
            self._invoke(
                invoker,
                generate_prd_command,
                input_file=str(idea_path),
                output=str(prd_output),
                interactive=False,
                auto_validate=False,
                preview=False,
                enable_ai=enable_ai,
                embedding_model=embedding_model,
            )
            prd_structured = prd_output / "prd_structured.json"
            if not prd_structured.exists():
                raise click.ClickException("Não foi possível localizar prd_structured.json após geração do PRD.")
            current_prd_path = prd_structured

        if current_prd_path and not current_prps_path and not tasks_from_us:
            echo("\n[Autopilot] Gerando PRPs a partir do PRD...")
            prps_output = project_path / "prps"
            prps_output.mkdir(parents=True, exist_ok=True)
            self._invoke(
                invoker,
                generate_prps_command,
                prd_file=str(current_prd_path),
                output=str(prps_output),
                parallel=False,
                interactive=False,
                auto_validate=False,
                preview=False,
                phase=None,
                enable_ai=enable_ai,
                embedding_model=embedding_model,
            )
            current_prps_path = prps_output

        if tasks_from_us:
            echo("\n[Autopilot] Gerando Tasks via User Story interativa...")
            tasks_output = project_path / "tasks"
            tasks_output.mkdir(parents=True, exist_ok=True)
            self._invoke(
                invoker,
                generate_tasks_command,
                prps_dir=None,
                output=str(tasks_output),
                interactive=True,
                from_us=True,
                enable_ai=enable_ai,
                embedding_model=embedding_model,
            )
            current_tasks_path = tasks_output
        elif current_prps_path and not current_tasks_path:
            echo("\n[Autopilot] Gerando Tasks a partir dos PRPs...")
            tasks_output = project_path / "tasks"
            tasks_output.mkdir(parents=True, exist_ok=True)
            self._invoke(
                invoker,
                generate_tasks_command,
                prps_dir=str(current_prps_path),
                output=str(tasks_output),
                interactive=False,
                from_us=False,
                enable_ai=enable_ai,
                embedding_model=embedding_model,
            )
            current_tasks_path = tasks_output
        elif not current_prps_path and not tasks_from_us and not current_tasks_path:
            echo("\n[Autopilot] Nenhum PRP disponível e --tasks-from-us não foi fornecido. Etapa de Tasks pulada.")

        if not skip_validate:
            if current_prps_path and current_prps_path.exists():
                echo("\n[Autopilot] Validando rastreabilidade...")
                self._invoke(
                    invoker,
                    validate_command,
                    prps_dir=str(current_prps_path),
                    enable_ai=enable_ai,
                    prd_file=str(current_prd_path) if current_prd_path else None,
                    tasks_dir=str(current_tasks_path) if current_tasks_path else None,
                    api_spec=None,
                    ui_tasks_dir=None,
                    soft_check=False,
                    dry_run=False,
                    help_contextual=False,
                    commits_json=None,
                    project_name=inferred_name,
                )
            else:
                echo("\n[Autopilot] Nenhum PRP disponível para validação automática. Etapa de validação foi ignorada.")

        return {
            "project_path": project_path,
            "prd_path": current_prd_path,
            "prps_path": current_prps_path,
            "tasks_path": current_tasks_path,
        }
