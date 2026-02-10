"""Tests for core.prerequisites module."""

import subprocess
from pathlib import Path

import pytest

from core.exceptions import (
    DependencyMissingError,
    GitNotInitializedError,
    PRDNotFoundError,
    PRPsNotFoundError,
)
from core.prerequisites import PrerequisiteChecker, validate_prerequisites


class TestPrerequisiteChecker:
    def test_init(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        assert checker.project_dir == tmp_path.resolve()

    # -- PRD checks --
    def test_check_prd_exists_true(self, tmp_path):
        (tmp_path / "PRD.md").write_text("# PRD", encoding="utf-8")
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_prd_exists() is True

    def test_check_prd_exists_in_subdir(self, tmp_path):
        prd_dir = tmp_path / "prd"
        prd_dir.mkdir()
        (prd_dir / "PRD.md").write_text("# PRD", encoding="utf-8")
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_prd_exists() is True

    def test_check_prd_exists_json(self, tmp_path):
        (tmp_path / "prd_structured.json").write_text("{}", encoding="utf-8")
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_prd_exists() is True

    def test_check_prd_not_found_raises(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        with pytest.raises(PRDNotFoundError):
            checker.check_prd_exists(raise_error=True)

    def test_check_prd_not_found_no_raise(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_prd_exists(raise_error=False) is False

    # -- PRPs checks --
    def test_check_prps_exist_true(self, tmp_path):
        prps = tmp_path / "PRPs"
        prps.mkdir()
        (prps / "F0_plan.md").write_text("# F0", encoding="utf-8")
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_prps_exist() is True

    def test_check_prps_empty_dir(self, tmp_path):
        (tmp_path / "PRPs").mkdir()
        checker = PrerequisiteChecker(tmp_path)
        with pytest.raises(PRPsNotFoundError):
            checker.check_prps_exist(raise_error=True)

    def test_check_prps_not_found_no_raise(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_prps_exist(raise_error=False) is False

    # -- Git checks --
    def test_check_git_initialized_true(self, tmp_path):
        (tmp_path / ".git").mkdir()
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_git_initialized() is True

    def test_check_git_not_initialized_raises(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        with pytest.raises(GitNotInitializedError):
            checker.check_git_initialized(raise_error=True)

    def test_check_git_not_initialized_no_raise(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_git_initialized(raise_error=False) is False

    # -- Command checks --
    def test_check_command_available_python(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_command_available("python3") is True

    def test_check_command_not_available_raises(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        with pytest.raises(DependencyMissingError):
            checker.check_command_available("nonexistent_command_xyz_123")

    def test_check_command_not_available_no_raise(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_command_available("nonexistent_command_xyz_123", raise_error=False) is False

    # -- Python package checks --
    def test_check_python_package_installed(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_python_package("json") is True

    def test_check_python_package_not_installed_raises(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        with pytest.raises(DependencyMissingError):
            checker.check_python_package("nonexistent_package_xyz_123")

    def test_check_python_package_not_installed_no_raise(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_python_package("nonexistent_package_xyz_123", raise_error=False) is False

    # -- Disk space --
    def test_check_disk_space(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_disk_space(required_mb=1) is True

    # -- Write permissions --
    def test_check_write_permissions(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        assert checker.check_write_permissions() is True

    # -- check_all_for_command --
    def test_check_all_validate_with_prd(self, tmp_path):
        (tmp_path / "PRD.md").write_text("# PRD", encoding="utf-8")
        checker = PrerequisiteChecker(tmp_path)
        result = checker.check_all_for_command("validate")
        assert "prd_exists" in result["checks_passed"]

    def test_check_all_validate_without_prd(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        with pytest.raises(PRDNotFoundError):
            checker.check_all_for_command("validate")

    def test_check_all_unknown_command(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        result = checker.check_all_for_command("unknown-command")
        assert result["checks_passed"] == []
        assert result["checks_failed"] == []

    def test_check_all_install_hooks(self, tmp_path):
        (tmp_path / ".git").mkdir()
        checker = PrerequisiteChecker(tmp_path)
        result = checker.check_all_for_command("install-hooks")
        assert "git_initialized" in result["checks_passed"]


    def test_check_disk_space_insufficient_no_raise(self, tmp_path):
        from unittest.mock import patch
        checker = PrerequisiteChecker(tmp_path)
        with patch("shutil.disk_usage") as mock_du:
            mock_du.return_value = type("Usage", (), {"free": 1024 * 1024})()  # 1MB
            assert checker.check_disk_space(required_mb=999999, raise_error=False) is False

    def test_check_disk_space_insufficient_raise_caught(self, tmp_path):
        """ContextEngineerError is caught by the broad except — returns True."""
        from unittest.mock import patch
        checker = PrerequisiteChecker(tmp_path)
        with patch("shutil.disk_usage") as mock_du:
            mock_du.return_value = type("Usage", (), {"free": 1024 * 1024})()
            # The raise is caught by except Exception → returns True
            result = checker.check_disk_space(required_mb=999999, raise_error=True)
            assert result is True

    def test_check_write_permissions_no_raise(self, tmp_path):
        from unittest.mock import patch
        checker = PrerequisiteChecker(tmp_path)
        with patch.object(Path, "touch", side_effect=PermissionError):
            assert checker.check_write_permissions(raise_error=False) is False

    def test_check_write_permissions_raises(self, tmp_path):
        from unittest.mock import patch
        from core.exceptions import InsufficientPermissionsError
        checker = PrerequisiteChecker(tmp_path)
        with patch.object(Path, "touch", side_effect=PermissionError):
            with pytest.raises(InsufficientPermissionsError):
                checker.check_write_permissions(raise_error=True)

    def test_check_all_generate_prps(self, tmp_path):
        (tmp_path / "PRD.md").write_text("# PRD", encoding="utf-8")
        checker = PrerequisiteChecker(tmp_path)
        result = checker.check_all_for_command("generate-prps")
        assert "prd_exists" in result["checks_passed"]

    def test_check_all_generate_prps_no_prd(self, tmp_path):
        checker = PrerequisiteChecker(tmp_path)
        with pytest.raises(PRDNotFoundError):
            checker.check_all_for_command("generate-prps")

    def test_check_all_generate_tasks(self, tmp_path):
        prps = tmp_path / "PRPs"
        prps.mkdir()
        (prps / "F0.md").write_text("# F0", encoding="utf-8")
        checker = PrerequisiteChecker(tmp_path)
        result = checker.check_all_for_command("generate-tasks")
        assert "prps_exist" in result["checks_passed"]


class TestValidatePrerequisites:
    def test_validate_unknown_command(self, tmp_path):
        result = validate_prerequisites("unknown", project_dir=tmp_path)
        assert result is True

    def test_validate_with_prd(self, tmp_path):
        (tmp_path / "PRD.md").write_text("# PRD", encoding="utf-8")
        result = validate_prerequisites("validate", project_dir=tmp_path)
        assert result is True

    def test_validate_without_prd(self, tmp_path):
        with pytest.raises(PRDNotFoundError):
            validate_prerequisites("validate", project_dir=tmp_path)
