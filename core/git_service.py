"""Git-related services extracted from the CLI layer."""

from __future__ import annotations

import os
import re
import stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

TASK_ID_PATTERN = re.compile(r"(FR-\d+|US-\d+|TASK-\d+)", re.IGNORECASE)


WarningHandler = Optional[Callable[[str], None]]


def _default_warning_handler(message: str) -> None:
    """Fallback warning handler when CLI feedback is not provided."""
    del message  # Intentionally ignore when no handler is supplied.


@dataclass
class HookGenerationResult:
    """Metadata produced after writing git hooks."""

    pre_push_path: Path
    pre_commit_path: Path
    mode_description: str


class GitService:
    """Encapsulates interactions with git history and working tree."""

    def __init__(self, project_dir: Path, warning_handler: WarningHandler = None) -> None:
        """
        Initialize the git service.

        Args:
            project_dir: Root directory of the git repository.
            warning_handler: Optional callback for non-blocking warnings.
        """
        self.project_dir = Path(project_dir).resolve()
        self.warning_handler = warning_handler or _default_warning_handler

    @staticmethod
    def extract_task_ids(content: str) -> set[str]:
        """Return the set of FR/US/TASK identifiers present in a string."""
        return {match.group(1).upper() for match in TASK_ID_PATTERN.finditer(content or "")}

    def build_commit_mapping(self, since: str | None = None, include_uncommitted: bool = True) -> dict:
        """
        Build a mapping between task identifiers and git commits.

        Args:
            since: Optional git revspec limiting the history traversal.
            include_uncommitted: Whether to include staged/untracked changes.

        Returns:
            Dictionary ready to be serialized into commits.json.
        """
        mapping: dict[str, dict[str, Any]] = {}

        def ensure_task(task_id: str) -> dict:
            return mapping.setdefault(
                task_id,
                {
                    "task_id": task_id,
                    "commits": [],
                    "pull_requests": [],
                },
            )

        def append_commit(task_id: str, commit_hash: str, message: str) -> None:
            task_entry = ensure_task(task_id)
            if not any(c["hash"] == commit_hash for c in task_entry["commits"]):
                task_entry["commits"].append({"hash": commit_hash, "message": message})

        def map_commit(commit_hash: str) -> None:
            try:
                show_cmd = [
                    "git",
                    "show",
                    "--no-color",
                    "--name-only",
                    "--pretty=format:%H%n%B",
                    commit_hash,
                ]
                result = subprocess.run(
                    show_cmd,
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                lines = result.stdout.splitlines()
                commit_id = lines[0].strip()
                message_lines: list[str] = []
                idx = 1
                while idx < len(lines) and lines[idx].strip():
                    message_lines.append(lines[idx])
                    idx += 1
                message = "\n".join(message_lines).strip()
                changed_files = [line.strip() for line in lines[idx + 1 :] if line.strip()]

                referenced_tasks: set[str] = set()
                referenced_tasks.update(self.extract_task_ids(message))
                for file_path in changed_files:
                    referenced_tasks.update(self.extract_task_ids(file_path))

                if not referenced_tasks:
                    referenced_tasks.add("UNMAPPED")

                for task_id in referenced_tasks:
                    append_commit(task_id, commit_id, message)
            except subprocess.CalledProcessError:
                self.warning_handler(f"[AVISO] Falha ao inspecionar commit {commit_hash}")

        try:
            rev_range = since or "HEAD"
            log_cmd = ["git", "log", "--pretty=format:%H", rev_range]
            result = subprocess.run(log_cmd, cwd=self.project_dir, capture_output=True, text=True, check=True)
            commit_hashes = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            for commit_hash in commit_hashes:
                map_commit(commit_hash)
        except subprocess.CalledProcessError:
            self.warning_handler("[AVISO] Não foi possível executar 'git log'.")

        if include_uncommitted:
            try:
                status_cmd = ["git", "status", "--porcelain"]
                status_result = subprocess.run(
                    status_cmd, cwd=self.project_dir, capture_output=True, text=True, check=True
                )
                for line in status_result.stdout.splitlines():
                    if not line.strip():
                        continue
                    file_path = line[3:].strip()
                    task_ids = self.extract_task_ids(file_path) or {"UNMAPPED"}
                    for task_id in task_ids:
                        entry = ensure_task(task_id)
                        if not any(c.get("hash") == "WORKTREE" for c in entry["commits"]):
                            entry["commits"].append({"hash": "WORKTREE", "message": "Uncommitted change"})
            except subprocess.CalledProcessError:
                self.warning_handler("[AVISO] Não foi possível executar 'git status'.")

        commit_mapping = sorted(mapping.values(), key=lambda item: item["task_id"])
        return {
            "project_name": self.project_dir.name,
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "commit_mapping": commit_mapping,
        }


class GitHookManager:
    """Handles creation of git hook scripts for Context Engineer."""

    def __init__(self, project_dir: Path, cli_command: str = "ce") -> None:
        """
        Initialize the hook manager.

        Args:
            project_dir: Project root containing the .git directory.
            cli_command: Command name used in generated hook scripts.
        """
        self.project_dir = Path(project_dir).resolve()
        self.cli_command = cli_command

    def generate_hooks(self, project_name: str, soft_gate: bool = True) -> HookGenerationResult:
        """
        Create pre-push and pre-commit hooks inside .git/hooks.

        Args:
            project_name: Name of the project used for reporting.
            soft_gate: Whether hooks should run in consultative mode.

        Returns:
            HookGenerationResult describing generated files.
        """
        git_hooks_dir = self.project_dir / ".git" / "hooks"
        git_hooks_dir.mkdir(parents=True, exist_ok=True)

        pre_push_hook = git_hooks_dir / "pre-push"
        pre_commit_hook = git_hooks_dir / "pre-commit"

        pre_push_hook.write_text(self._render_pre_push_hook(project_name, soft_gate), encoding="utf-8")
        pre_commit_hook.write_text(self._render_pre_commit_hook(), encoding="utf-8")

        os.chmod(pre_push_hook, os.stat(pre_push_hook).st_mode | stat.S_IEXEC)
        os.chmod(pre_commit_hook, os.stat(pre_commit_hook).st_mode | stat.S_IEXEC)

        mode_text = "Soft-Gate (consultivo)" if soft_gate else "Hard-Gate (bloqueante)"
        return HookGenerationResult(pre_push_hook, pre_commit_hook, mode_text)

    def _render_pre_push_hook(self, project_name: str, soft_gate: bool) -> str:
        project_dir = self.project_dir.absolute()
        command = self.cli_command

        if soft_gate:
            return f"""#!/bin/bash
# Context Engineer - Pre-Push Validation Hook (Soft-Gate Mode)
# Generated automatically by '{command} init' or '{command} install-hooks'
# Consultive validation: warns about issues and asks for confirmation

PROJECT_DIR="{project_dir}"
PROJECT_NAME="{project_name}"
VALIDATION_FAILED=0

echo ""
echo " Context Engineer: Validando rastreabilidade antes do push..."
echo ""

# Check if ce command is available
if ! command -v {command} &> /dev/null; then
 echo "Context Engineer CLI não encontrado."
 echo " Execute: pip install -e ."
 echo " Continuando com push (sem validação)..."
 exit 0
fi

COMMITS_FILE="$PROJECT_DIR/commits.json"
COMMITS_ARGS=""
echo "Gerando commits.json para rastreabilidade inversa..."
if {command} generate-commit-map --project-dir "$PROJECT_DIR" --output "$COMMITS_FILE" >/dev/null 2>&1; then
 if [ -f "$COMMITS_FILE" ]; then
 COMMITS_ARGS="--commits-json \\"$COMMITS_FILE\\""
 fi
else
 echo "[AVISO] Não foi possível gerar commits.json automaticamente."
fi

# Validate PRPs if they exist
if [ -d "$PROJECT_DIR/PRPs" ]; then
 echo "Validando PRPs e rastreabilidade..."
 {command} validate "$PROJECT_DIR/PRPs" --soft-check $COMMITS_ARGS 2>&1
 VALIDATION_EXIT_CODE=$?
 
 if [ $VALIDATION_EXIT_CODE -ne 0 ]; then
 VALIDATION_FAILED=1
 echo ""
 echo "ATENÇÃO: Foram encontradas inconsistências de rastreabilidade!"
 echo ""
 echo " Isso pode dificultar o trabalho da IA nas próximas fases (F5-F11)."
 echo " A quebra de rastreabilidade prejudica:"
 echo " • Context Pruning (compressão inteligente de contexto)"
 echo " • Deep Cross-Validation (detecção de broken contracts)"
 echo " • Estimativas precisas baseadas em histórico"
 echo ""
 fi
fi

# Validate contract integrity if OpenAPI spec exists
if [ -f "$PROJECT_DIR/PRPs/openapi.yaml" ] && [ -d "$PROJECT_DIR/TASKs" ]; then
 echo "Validando integridade de contratos (Deep Cross-Validation)..."
 {command} validate "$PROJECT_DIR/PRPs" \\
 --api-spec "$PROJECT_DIR/PRPs/openapi.yaml" \\
 --ui-tasks-dir "$PROJECT_DIR/TASKs" \\
 $COMMITS_ARGS \\
 --soft-check 2>&1
 CONTRACT_EXIT_CODE=$?
 
 if [ $CONTRACT_EXIT_CODE -ne 0 ]; then
 VALIDATION_FAILED=1
 echo ""
 echo "ATENÇÃO: Foram encontrados contratos quebrados!"
 echo ""
 echo " Isso pode causar erros em runtime quando a UI tentar usar endpoints"
 echo " que não existem mais ou mudaram de assinatura."
 echo ""
 fi
fi

# If validation failed, show metrics summary and ask for confirmation
if [ $VALIDATION_FAILED -eq 1 ]; then
 echo ""
 echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
 echo ""
 
 # Show metrics summary for quantitative context
 if [ -d "$PROJECT_DIR/TASKs" ]; then
 echo "Contexto Quantitativo da Fase Atual:"
 {command} metrics-summary --project-name "$PROJECT_NAME" --tasks-dir "$PROJECT_DIR/TASKs" 2>/dev/null || echo " (Métricas não disponíveis)"
 else
 echo "Contexto Quantitativo da Fase Atual:"
 {command} metrics-summary --project-name "$PROJECT_NAME" 2>/dev/null || echo " (Métricas não disponíveis)"
 fi
 
 echo ""
 echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
 echo ""
 read -p "Deseja prosseguir com o push mesmo assim? (y/n) " -n 1 -r
 echo ""
 echo ""
 
 if [[ ! $REPLY =~ ^[Yy]$ ]]; then
 echo "Push cancelado para correção da rastreabilidade."
 echo " Use '{command} validate' para ver detalhes dos problemas."
 echo ""
 exit 1
 else
 echo "Prosseguindo com push (validação ignorada)."
 echo " Recomendação: Corrija os problemas antes do próximo push."
 echo ""
 fi
else
 echo "Validação concluída com sucesso!"
 echo ""
fi

exit 0
"""

        return f"""#!/bin/bash
# Context Engineer - Pre-Push Validation Hook (Hard-Gate Mode)
# Blocks push if validation fails

set -e

PROJECT_DIR="{project_dir}"
PROJECT_NAME="{project_name}"

echo "Context Engineer: Validando antes do push..."

# Check if ce command is available
if ! command -v {command} &> /dev/null; then
 echo "Context Engineer CLI não encontrado. Instalando..."
 echo " Execute: pip install -e ."
 exit 0
fi

COMMITS_FILE="$PROJECT_DIR/commits.json"
COMMITS_ARGS=""
echo "Gerando commits.json para rastreabilidade inversa..."
if {command} generate-commit-map --project-dir "$PROJECT_DIR" --output "$COMMITS_FILE" >/dev/null 2>&1; then
 if [ -f "$COMMITS_FILE" ]; then
 COMMITS_ARGS="--commits-json \\"$COMMITS_FILE\\""
 fi
else
 echo "[AVISO] Não foi possível gerar commits.json automaticamente."
fi

# Validate PRPs if they exist
if [ -d "$PROJECT_DIR/PRPs" ]; then
 echo "Validando PRPs..."
 {command} validate "$PROJECT_DIR/PRPs" $COMMITS_ARGS || {{
 echo "Validação de PRPs falhou!"
 echo " Corrija os erros antes de fazer push."
 exit 1
 }}
fi

# Validate contract integrity if OpenAPI spec exists
if [ -f "$PROJECT_DIR/PRPs/openapi.yaml" ] && [ -d "$PROJECT_DIR/TASKs" ]; then
 echo "Validando integridade de contratos..."
 {command} validate "$PROJECT_DIR/PRPs" \\
 --api-spec "$PROJECT_DIR/PRPs/openapi.yaml" \\
 --ui-tasks-dir "$PROJECT_DIR/TASKs" \\
 $COMMITS_ARGS || {{
 echo "Validação de contratos falhou!"
 echo " Corrija os contratos quebrados antes de fazer push."
 exit 1
 }}
fi

echo "Validação concluída com sucesso!"
exit 0
"""

    def _render_pre_commit_hook(self) -> str:
        project_dir = self.project_dir.absolute()
        return f"""#!/bin/bash
# Context Engineer - Pre-Commit Validation Hook
# Quick validation before commit

set -e

PROJECT_DIR="{project_dir}"

# Quick syntax check if PRPs exist
if [ -d "$PROJECT_DIR/PRPs" ]; then
 # Check for obvious JSON/YAML syntax errors
 for file in "$PROJECT_DIR/PRPs"/*.json; do
 if [ -f "$file" ]; then
 python3 -m json.tool "$file" > /dev/null 2>&1 || {{
 echo "Erro de sintaxe JSON em: $file"
 exit 1
 }}
 fi
 done
fi

exit 0
"""
