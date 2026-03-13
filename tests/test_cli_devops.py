"""Tests for cli.commands.devops module."""

import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from cli.commands.devops import ci_bootstrap, install_hooks, git_setup, mock_server


class TestCiBootstrap:
    def test_ci_bootstrap_success(self, tmp_path):
        runner = CliRunner()
        template = tmp_path / "docs" / "ci_bootstrap_template.yml"
        template.parent.mkdir(parents=True)
        template.write_text("name: CI\non: push\n", encoding="utf-8")
        with patch("cli.commands.devops.REPO_ROOT", tmp_path):
            result = runner.invoke(ci_bootstrap, ["--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "Workflow created" in result.output

    def test_ci_bootstrap_no_template(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.devops.REPO_ROOT", tmp_path):
            result = runner.invoke(ci_bootstrap, ["--project-dir", str(tmp_path)])
        assert result.exit_code != 0
        assert "CI template not found" in result.output


class TestInstallHooks:
    def test_install_hooks_no_git(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(install_hooks, ["--project-dir", str(tmp_path)])
        assert result.exit_code != 0

    def test_install_hooks_success(self, tmp_path):
        (tmp_path / ".git" / "hooks").mkdir(parents=True)
        runner = CliRunner()
        with patch("cli.commands.devops.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=1, stdout="")
            result = runner.invoke(install_hooks, ["--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "hooks installed" in result.output

    def test_install_hooks_hard_gate(self, tmp_path):
        (tmp_path / ".git" / "hooks").mkdir(parents=True)
        runner = CliRunner()
        with patch("cli.commands.devops.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=1, stdout="")
            result = runner.invoke(install_hooks, ["--project-dir", str(tmp_path), "--hard-gate"])
        assert result.exit_code == 0
        assert "Hard-Gate" in result.output


class TestMockServer:
    def test_mock_server_success(self, tmp_path):
        runner = CliRunner()
        spec = tmp_path / "openapi.json"
        spec.write_text('{"openapi": "3.0.0"}', encoding="utf-8")
        with patch("cli.commands.devops.PRPValidator") as MockValidator:
            mock_instance = MockValidator.return_value
            mock_instance.generate_transient_mock.return_value = {
                "success": True,
                "message": "Mock server started",
                "mock_url": "http://localhost:4010",
                "process_id": 12345,
            }
            result = runner.invoke(mock_server, [str(spec)])
        assert result.exit_code == 0
        assert "Mock server started" in result.output

    def test_mock_server_failure(self, tmp_path):
        runner = CliRunner()
        spec = tmp_path / "openapi.json"
        spec.write_text('{"openapi": "3.0.0"}', encoding="utf-8")
        with patch("cli.commands.devops.PRPValidator") as MockValidator:
            mock_instance = MockValidator.return_value
            mock_instance.generate_transient_mock.return_value = {
                "success": False,
                "errors": ["Prism not found"],
                "warnings": ["Install prism CLI"],
                "command": "npx prism mock openapi.json",
            }
            result = runner.invoke(mock_server, [str(spec)])
        assert result.exit_code != 0
        assert "Prism not found" in result.output


class TestGitSetup:
    def test_git_setup_already_initialized_with_identity(self, tmp_path):
        """Git already init, has remote, has identity, skip hooks."""
        (tmp_path / ".git" / "hooks").mkdir(parents=True)
        runner = CliRunner()
        with patch("cli.commands.devops.subprocess") as mock_sub:
            def fake_run(cmd, **kwargs):
                cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
                if "remote" in cmd_str and "get-url" in cmd_str:
                    return MagicMock(returncode=0, stdout="https://github.com/user/repo.git")
                if "branch" in cmd_str:
                    return MagicMock(returncode=0, stdout="main")
                if "user.name" in cmd_str and "config" in cmd_str and len(cmd) == 3:
                    return MagicMock(returncode=0, stdout="Test User")
                if "user.email" in cmd_str and "config" in cmd_str and len(cmd) == 3:
                    return MagicMock(returncode=0, stdout="test@example.com")
                return MagicMock(returncode=0, stdout="")
            mock_sub.run.side_effect = fake_run
            # Prompts: change remote? n, install hooks? n
            result = runner.invoke(git_setup, ["--project-dir", str(tmp_path)], input="n\nn\n")
        assert result.exit_code == 0
        assert "Git setup complete" in result.output

    def test_git_setup_no_remote_no_identity(self, tmp_path):
        """Git init exists, no remote, no identity — user skips all."""
        (tmp_path / ".git" / "hooks").mkdir(parents=True)
        runner = CliRunner()
        with patch("cli.commands.devops.subprocess") as mock_sub:
            def fake_run(cmd, **kwargs):
                cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
                if "remote" in cmd_str and "get-url" in cmd_str:
                    return MagicMock(returncode=1, stdout="")
                if "branch" in cmd_str:
                    return MagicMock(returncode=1, stdout="")
                if "user.name" in cmd_str and "config" in cmd_str and len(cmd) == 3:
                    return MagicMock(returncode=1, stdout="")
                if "user.email" in cmd_str and "config" in cmd_str and len(cmd) == 3:
                    return MagicMock(returncode=1, stdout="")
                return MagicMock(returncode=0, stdout="")
            mock_sub.run.side_effect = fake_run
            # Prompts: add remote? n, name, email, install hooks? n
            result = runner.invoke(git_setup, ["--project-dir", str(tmp_path)], input="n\nTest\ntest@test.com\nn\n")
        assert result.exit_code == 0
        assert "Git setup complete" in result.output

    def test_git_setup_init_then_add_remote_and_hooks(self, tmp_path):
        """User inits git, adds remote, sets identity, installs hooks."""
        runner = CliRunner()
        with patch("cli.commands.devops.subprocess") as mock_sub:
            call_count = [0]

            def fake_run(cmd, **kwargs):
                call_count[0] += 1
                cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
                if "init" in cmd_str:
                    (tmp_path / ".git" / "hooks").mkdir(parents=True, exist_ok=True)
                    return MagicMock(returncode=0, stdout="")
                if "remote" in cmd_str and "get-url" in cmd_str:
                    return MagicMock(returncode=1, stdout="")
                if "remote" in cmd_str and "add" in cmd_str:
                    return MagicMock(returncode=0, stdout="")
                if "branch" in cmd_str:
                    return MagicMock(returncode=1, stdout="")
                if "user.name" in cmd_str and "config" in cmd_str:
                    if len(cmd) == 3:
                        return MagicMock(returncode=1, stdout="")
                    return MagicMock(returncode=0, stdout="")
                if "user.email" in cmd_str and "config" in cmd_str:
                    if len(cmd) == 3:
                        return MagicMock(returncode=1, stdout="")
                    return MagicMock(returncode=0, stdout="")
                return MagicMock(returncode=0, stdout="")

            mock_sub.run.side_effect = fake_run
            with patch("cli.commands.devops._generate_git_hooks"):
                # y=init, y=add remote, url, Dev Name, dev@email, y=hooks, n=hard-gate
                result = runner.invoke(
                    git_setup,
                    ["--project-dir", str(tmp_path)],
                    input="y\ny\nhttps://github.com/user/repo.git\nDev\ndev@test.com\ny\nn\n",
                )
        assert result.exit_code == 0
        assert "Git setup complete" in result.output

    def test_git_setup_change_remote(self, tmp_path):
        """User changes existing remote."""
        (tmp_path / ".git" / "hooks").mkdir(parents=True)
        runner = CliRunner()
        with patch("cli.commands.devops.subprocess") as mock_sub:
            def fake_run(cmd, **kwargs):
                cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
                if "remote" in cmd_str and "get-url" in cmd_str:
                    return MagicMock(returncode=0, stdout="https://old.git")
                if "remote" in cmd_str and "set-url" in cmd_str:
                    return MagicMock(returncode=0, stdout="")
                if "branch" in cmd_str:
                    return MagicMock(returncode=0, stdout="main")
                if "user.name" in cmd_str:
                    return MagicMock(returncode=0, stdout="Dev")
                if "user.email" in cmd_str:
                    return MagicMock(returncode=0, stdout="dev@test.com")
                return MagicMock(returncode=0, stdout="")
            mock_sub.run.side_effect = fake_run
            # y=change remote, new url, n=hooks
            result = runner.invoke(
                git_setup,
                ["--project-dir", str(tmp_path)],
                input="y\nhttps://new.git\nn\n",
            )
        assert result.exit_code == 0

    def test_git_setup_skip_init(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(git_setup, ["--project-dir", str(tmp_path)], input="n\n")
        assert result.exit_code == 0
        assert "Skipping" in result.output
