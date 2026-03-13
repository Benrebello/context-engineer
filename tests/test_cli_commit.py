"""Tests for cli.commands.commit module."""

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from cli.commands.commit import generate_commit_map

PATCH_TARGET = "cli.commands.commit.build_commit_mapping"


class TestGenerateCommitMap:
    def test_no_git_dir(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(generate_commit_map, ["--project-dir", str(tmp_path)])
        assert result.exit_code != 0

    def test_with_git_dir(self, tmp_path):
        (tmp_path / ".git").mkdir()
        runner = CliRunner()
        with patch(PATCH_TARGET, return_value={"tasks": {}, "unmapped_commits": []}):
            result = runner.invoke(generate_commit_map, [
                "--project-dir", str(tmp_path),
                "--output", str(tmp_path / "commits.json"),
            ])
        assert result.exit_code == 0
        assert "Commit map saved" in result.output

    def test_with_git_range(self, tmp_path):
        (tmp_path / ".git").mkdir()
        runner = CliRunner()
        with patch(PATCH_TARGET, return_value={"tasks": {}}):
            result = runner.invoke(generate_commit_map, [
                "--project-dir", str(tmp_path),
                "--git-range", "origin/main..HEAD",
                "--output", str(tmp_path / "commits.json"),
            ])
        assert result.exit_code == 0

    def test_skip_uncommitted(self, tmp_path):
        (tmp_path / ".git").mkdir()
        runner = CliRunner()
        with patch(PATCH_TARGET, return_value={"tasks": {}}):
            result = runner.invoke(generate_commit_map, [
                "--project-dir", str(tmp_path),
                "--skip-uncommitted",
                "--output", str(tmp_path / "commits.json"),
            ])
        assert result.exit_code == 0

    def test_build_error(self, tmp_path):
        (tmp_path / ".git").mkdir()
        runner = CliRunner()
        with patch(PATCH_TARGET, side_effect=RuntimeError("git error")):
            result = runner.invoke(generate_commit_map, [
                "--project-dir", str(tmp_path),
                "--output", str(tmp_path / "commits.json"),
            ])
        assert result.exit_code == 1
