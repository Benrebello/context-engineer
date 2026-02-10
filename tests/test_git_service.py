"""Tests for core.git_service module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.git_service import GitHookManager, GitService, TASK_ID_PATTERN


class TestTaskIdPattern:
    def test_extract_fr_ids(self):
        text = "Implemented FR-001 and FR-002 features"
        ids = GitService.extract_task_ids(text)
        assert "FR-001" in ids
        assert "FR-002" in ids

    def test_extract_us_ids(self):
        text = "Closes US-010"
        ids = GitService.extract_task_ids(text)
        assert "US-010" in ids

    def test_extract_task_ids(self):
        text = "TASK-005 completed"
        ids = GitService.extract_task_ids(text)
        assert "TASK-005" in ids

    def test_extract_mixed(self):
        text = "FR-001 US-002 TASK-003"
        ids = GitService.extract_task_ids(text)
        assert len(ids) == 3

    def test_extract_empty(self):
        assert GitService.extract_task_ids("") == set()
        assert GitService.extract_task_ids(None) == set()

    def test_case_insensitive(self):
        text = "fr-001 us-002"
        ids = GitService.extract_task_ids(text)
        assert "FR-001" in ids
        assert "US-002" in ids


class TestGitService:
    def test_init(self, tmp_path):
        svc = GitService(tmp_path)
        assert svc.project_dir == tmp_path.resolve()

    def test_init_with_warning_handler(self, tmp_path):
        warnings = []
        svc = GitService(tmp_path, warning_handler=warnings.append)
        svc.warning_handler("test warning")
        assert "test warning" in warnings

    def test_default_warning_handler(self, tmp_path):
        svc = GitService(tmp_path)
        # Should not raise
        svc.warning_handler("ignored message")

    def test_build_commit_mapping_no_git(self, tmp_path):
        warnings = []
        svc = GitService(tmp_path, warning_handler=warnings.append)
        result = svc.build_commit_mapping(include_uncommitted=False)
        assert "project_name" in result
        assert "generated_at" in result
        assert "commit_mapping" in result

    def test_build_commit_mapping_with_git(self, tmp_path):
        # Initialize a real git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True, check=True)

        # Create a file and commit
        (tmp_path / "FR-001_feature.py").write_text("# feature", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "feat: FR-001 initial"], cwd=tmp_path, capture_output=True, check=True)

        svc = GitService(tmp_path)
        result = svc.build_commit_mapping(include_uncommitted=False)
        assert result["project_name"] == tmp_path.name
        assert len(result["commit_mapping"]) >= 1

    def test_build_commit_mapping_uncommitted(self, tmp_path):
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True, check=True)

        # Create initial commit
        (tmp_path / "README.md").write_text("# test", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create uncommitted file
        (tmp_path / "FR-002_new.py").write_text("# new", encoding="utf-8")

        svc = GitService(tmp_path)
        result = svc.build_commit_mapping(include_uncommitted=True)
        mapping = result["commit_mapping"]
        # Should have at least UNMAPPED from init commit
        assert len(mapping) >= 1


class TestGitHookManager:
    def test_generate_hooks_soft_gate(self, tmp_path):
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)

        manager = GitHookManager(tmp_path)
        result = manager.generate_hooks("test-project", soft_gate=True)

        assert result.pre_push_path.exists()
        assert result.pre_commit_path.exists()
        assert "Soft-Gate" in result.mode_description

        content = result.pre_push_path.read_text()
        assert "Soft-Gate" in content
        assert "test-project" in content

    def test_generate_hooks_hard_gate(self, tmp_path):
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)

        manager = GitHookManager(tmp_path)
        result = manager.generate_hooks("test-project", soft_gate=False)

        assert result.pre_push_path.exists()
        content = result.pre_push_path.read_text()
        assert "Hard-Gate" in content

    def test_hooks_are_executable(self, tmp_path):
        import os
        import stat

        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)

        manager = GitHookManager(tmp_path)
        result = manager.generate_hooks("proj")

        pre_push_mode = os.stat(result.pre_push_path).st_mode
        assert pre_push_mode & stat.S_IEXEC

    def test_pre_commit_hook_content(self, tmp_path):
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)

        manager = GitHookManager(tmp_path)
        result = manager.generate_hooks("proj")

        content = result.pre_commit_path.read_text()
        assert "pre-commit" in content.lower() or "Pre-Commit" in content
        assert "json.tool" in content

    def test_custom_cli_command(self, tmp_path):
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)

        manager = GitHookManager(tmp_path, cli_command="context-engineer")
        result = manager.generate_hooks("proj")

        content = result.pre_push_path.read_text()
        assert "context-engineer" in content
