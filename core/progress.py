"""
Progress tracking utilities for long-running operations.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

try:
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskID,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Progress = None  # type: ignore
    TaskID = Any  # type: ignore


class ProgressTracker:
    """Wrapper for progress tracking with fallback to simple output."""

    def __init__(self, enabled: bool = True):
        """
        Initialize progress tracker.

        Args:
            enabled: Whether to show progress (can be disabled for testing)
        """
        self.enabled = enabled and RICH_AVAILABLE
        self._progress: Progress | None = None
        self._tasks: dict[str, TaskID] = {}

    def __enter__(self) -> ProgressTracker:
        """Enter context manager."""
        if self.enabled:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
            )
            self._progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self._progress:
            self._progress.__exit__(exc_type, exc_val, exc_tb)

    def add_task(
        self,
        description: str,
        total: int | None = None,
        task_id: str | None = None,
    ) -> str:
        """
        Add a new task to track.

        Args:
            description: Task description
            total: Total number of steps (None for indeterminate)
            task_id: Optional task identifier

        Returns:
            Task ID for updating progress
        """
        if not self.enabled or not self._progress:
            # Fallback: just print the description
            print(f"[*] {description}...")
            return task_id or description

        task = self._progress.add_task(description, total=total)
        if task_id:
            self._tasks[task_id] = task
        return task_id or str(task)

    def update(
        self,
        task_id: str,
        advance: int = 1,
        description: str | None = None,
        completed: int | None = None,
    ) -> None:
        """
        Update task progress.

        Args:
            task_id: Task identifier
            advance: Number of steps to advance
            description: Optional new description
            completed: Optional absolute completed count
        """
        if not self.enabled or not self._progress:
            if description:
                print(f"  [OK] {description}")
            return

        task = self._tasks.get(task_id)
        if task is not None:
            kwargs = {}
            if advance:
                kwargs["advance"] = advance
            if description:
                kwargs["description"] = description
            if completed is not None:
                kwargs["completed"] = completed
            self._progress.update(task, **kwargs)

    def complete(self, task_id: str, description: str | None = None) -> None:
        """
        Mark task as complete.

        Args:
            task_id: Task identifier
            description: Optional completion message
        """
        if not self.enabled or not self._progress:
            msg = description or "Complete"
            print(f"  [OK] {msg}")
            return

        task = self._tasks.get(task_id)
        if task is not None:
            if description:
                self._progress.update(task, description=description)
            # Mark as 100% complete
            task_obj = self._progress.tasks[task]
            if task_obj.total:
                self._progress.update(task, completed=task_obj.total)


@contextmanager
def progress_context(description: str, total: int | None = None, enabled: bool = True):
    """
    Context manager for simple progress tracking.

    Args:
        description: Task description
        total: Total steps
        enabled: Whether progress is enabled

    Example:
        with progress_context("Processing files", total=10) as progress:
            for i in range(10):
                # Do work
                progress.update(advance=1)
    """
    tracker = ProgressTracker(enabled=enabled)
    with tracker:
        task_id = tracker.add_task(description, total=total, task_id="main")
        yield tracker
        tracker.complete("main")


class SimpleSpinner:
    """Simple spinner for operations without known duration."""

    def __init__(self, description: str, enabled: bool = True):
        """
        Initialize spinner.

        Args:
            description: Operation description
            enabled: Whether to show spinner
        """
        self.description = description
        self.enabled = enabled and RICH_AVAILABLE
        self._progress: Progress | None = None
        self._task: TaskID | None = None

    def __enter__(self) -> SimpleSpinner:
        """Start spinner."""
        if self.enabled:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            )
            self._progress.__enter__()
            self._task = self._progress.add_task(self.description)
        else:
            print(f"[*] {self.description}...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop spinner."""
        if self._progress:
            self._progress.__exit__(exc_type, exc_val, exc_tb)
        if not exc_type:
            print(f"  [OK] {self.description} - Done")

    def update(self, description: str) -> None:
        """
        Update spinner description.

        Args:
            description: New description
        """
        self.description = description
        if self._progress and self._task is not None:
            self._progress.update(self._task, description=description)


def create_progress_bar(
    description: str,
    total: int,
    enabled: bool = True,
) -> ProgressTracker:
    """
    Create a progress bar for tracking operations.

    Args:
        description: Operation description
        total: Total number of steps
        enabled: Whether to show progress

    Returns:
        ProgressTracker instance

    Example:
        progress = create_progress_bar("Generating PRPs", total=10)
        with progress:
            task_id = progress.add_task("Processing", total=10)
            for i in range(10):
                # Do work
                progress.update(task_id, advance=1)
    """
    tracker = ProgressTracker(enabled=enabled)
    return tracker


__all__ = [
    "ProgressTracker",
    "progress_context",
    "SimpleSpinner",
    "create_progress_bar",
    "RICH_AVAILABLE",
]
