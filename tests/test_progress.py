"""Tests for core.progress module."""

from pathlib import Path

import pytest

from core.progress import ProgressTracker, SimpleSpinner, progress_context, create_progress_bar


class TestProgressTrackerDisabled:
    """Test ProgressTracker when disabled (no rich)."""

    def test_init_disabled(self):
        tracker = ProgressTracker(enabled=False)
        assert tracker.enabled is False

    def test_context_manager_disabled(self):
        tracker = ProgressTracker(enabled=False)
        with tracker:
            pass

    def test_add_task_disabled(self, capsys):
        tracker = ProgressTracker(enabled=False)
        with tracker:
            task_id = tracker.add_task("Test task", total=5)
        captured = capsys.readouterr()
        assert "Test task" in captured.out

    def test_add_task_with_id(self, capsys):
        tracker = ProgressTracker(enabled=False)
        with tracker:
            task_id = tracker.add_task("Test task", total=5, task_id="my_task")
            assert task_id == "my_task"

    def test_update_disabled(self, capsys):
        tracker = ProgressTracker(enabled=False)
        with tracker:
            tracker.add_task("Test", task_id="t1")
            tracker.update("t1", advance=1)

    def test_update_with_description(self, capsys):
        tracker = ProgressTracker(enabled=False)
        with tracker:
            tracker.add_task("Test", task_id="t1")
            tracker.update("t1", description="Step 1 done")
        captured = capsys.readouterr()
        assert "Step 1 done" in captured.out

    def test_complete_disabled(self, capsys):
        tracker = ProgressTracker(enabled=False)
        with tracker:
            tracker.add_task("Test", task_id="t1")
            tracker.complete("t1")
        captured = capsys.readouterr()
        assert "Complete" in captured.out

    def test_complete_with_description(self, capsys):
        tracker = ProgressTracker(enabled=False)
        with tracker:
            tracker.add_task("Test", task_id="t1")
            tracker.complete("t1", description="All done!")
        captured = capsys.readouterr()
        assert "All done!" in captured.out


class TestSimpleSpinner:
    def test_spinner_disabled(self, capsys):
        spinner = SimpleSpinner("Loading", enabled=False)
        with spinner:
            spinner.update("Still loading")

    def test_spinner_context_manager(self):
        with SimpleSpinner("Test", enabled=False) as s:
            assert s.description == "Test"
            s.update("Updated")
            assert s.description == "Updated"


class TestProgressContext:
    def test_context_disabled(self, capsys):
        with progress_context("Processing", total=3, enabled=False) as tracker:
            tracker.update("main", advance=1)
        captured = capsys.readouterr()
        assert "Processing" in captured.out


class TestProgressTrackerWithRich:
    """Test ProgressTracker when rich IS available."""

    @pytest.fixture(autouse=True)
    def _skip_if_no_rich(self):
        try:
            from rich.progress import Progress
        except ImportError:
            pytest.skip("rich not installed")

    def test_context_manager_enabled(self):
        tracker = ProgressTracker(enabled=True)
        with tracker:
            task_id = tracker.add_task("Test", total=5, task_id="t1")
            tracker.update("t1", advance=1)
            tracker.update("t1", description="Step 2", advance=1)
            tracker.update("t1", completed=5)
            tracker.complete("t1", description="Done")

    def test_complete_without_description(self):
        tracker = ProgressTracker(enabled=True)
        with tracker:
            tracker.add_task("Test", total=3, task_id="t1")
            tracker.complete("t1")

    def test_update_unknown_task(self):
        tracker = ProgressTracker(enabled=True)
        with tracker:
            tracker.update("nonexistent", advance=1)
            tracker.complete("nonexistent")


class TestSimpleSpinnerWithRich:
    @pytest.fixture(autouse=True)
    def _skip_if_no_rich(self):
        try:
            from rich.progress import Progress
        except ImportError:
            pytest.skip("rich not installed")

    def test_spinner_enabled(self):
        spinner = SimpleSpinner("Loading", enabled=True)
        with spinner:
            spinner.update("Still loading")


class TestCreateProgressBar:
    def test_create_progress_bar(self):
        tracker = create_progress_bar("Test", total=10, enabled=False)
        assert isinstance(tracker, ProgressTracker)

    def test_create_progress_bar_disabled(self):
        tracker = create_progress_bar("Test", total=10, enabled=False)
        assert tracker.enabled is False
