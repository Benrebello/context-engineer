"""
Wave-Based Parallel Task Executor
Organizes tasks into dependency-aware waves for parallel execution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TaskNode:
    """Represents a single task with its dependencies."""

    task_id: str
    name: str
    dependencies: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    status: str = "pending"
    parallel_marker: bool = False  # [P] marker from Spec-Kit

    @property
    def is_independent(self) -> bool:
        """A task is independent if it has no unresolved dependencies."""
        return len(self.dependencies) == 0


@dataclass
class Wave:
    """A group of tasks that can execute in parallel."""

    wave_number: int
    tasks: list[TaskNode] = field(default_factory=list)

    @property
    def task_ids(self) -> list[str]:
        return [t.task_id for t in self.tasks]

    def __repr__(self) -> str:
        ids = ", ".join(self.task_ids)
        return f"Wave {self.wave_number}: [{ids}]"


class WaveExecutor:
    """
    Organizes tasks into waves based on dependency analysis.

    Tasks without dependencies run first. Subsequent waves contain
    tasks whose dependencies were satisfied in earlier waves.

    Example:
        Wave 1 (parallel): [User Model, Product Model]
        Wave 2 (parallel): [Orders API, Cart API]  (depend on models)
        Wave 3:            [Checkout UI]            (depends on APIs)
    """

    def __init__(self) -> None:
        self.tasks: dict[str, TaskNode] = {}
        self.waves: list[Wave] = []

    def add_task(self, task: TaskNode) -> None:
        """Register a task for wave planning."""
        self.tasks[task.task_id] = task

    def add_tasks_from_dict(self, tasks_data: list[dict[str, Any]]) -> None:
        """
        Bulk-add tasks from a list of task dictionaries.

        Expected format per item:
            {"task_id": "...", "name": "...", "dependencies": [...], "files": [...]}
        """
        for data in tasks_data:
            node = TaskNode(
                task_id=data.get("task_id", ""),
                name=str(data.get("name", data.get("objective", ""))),
                dependencies=data.get("dependencies", []),
                files=data.get("files", []),
                parallel_marker=data.get("parallel", False),
            )
            self.add_task(node)

    def build_waves(self) -> list[Wave]:
        """
        Organize all registered tasks into execution waves.

        Uses topological sorting: tasks with no pending dependencies
        are grouped into the current wave. Once a wave is "executed",
        its tasks are removed from the dependency lists of remaining tasks.

        Returns:
            Ordered list of Wave objects.
        """
        self.waves = []
        remaining = dict(self.tasks)
        resolved: set[str] = set()
        wave_number = 0

        while remaining:
            wave_number += 1
            current_wave = Wave(wave_number=wave_number)

            # Find all tasks whose dependencies are fully resolved
            ready = [
                task
                for task in remaining.values()
                if all(dep in resolved for dep in task.dependencies)
            ]

            if not ready:
                # Circular dependency detected — force remaining into one wave
                logger.warning(
                    "Circular dependency detected among: %s",
                    list(remaining.keys()),
                )
                current_wave.tasks = list(remaining.values())
                self.waves.append(current_wave)
                break

            # Also detect file conflicts: tasks touching the same files
            # should be in the same wave but executed sequentially
            file_groups: dict[str, list[TaskNode]] = {}
            for task in ready:
                for f in task.files:
                    file_groups.setdefault(f, []).append(task)

            current_wave.tasks = ready
            self.waves.append(current_wave)

            for task in ready:
                resolved.add(task.task_id)
                remaining.pop(task.task_id, None)

        return self.waves

    def get_execution_plan(self) -> str:
        """Generate a human-readable execution plan."""
        if not self.waves:
            self.build_waves()

        lines = ["# Execution Plan (Wave-Based)\n"]
        for wave in self.waves:
            parallel_label = " (parallel)" if len(wave.tasks) > 1 else ""
            lines.append(f"## Wave {wave.wave_number}{parallel_label}\n")
            for task in wave.tasks:
                deps = ", ".join(task.dependencies) if task.dependencies else "none"
                lines.append(f"- **{task.task_id}**: {task.name}")
                lines.append(f"  - Dependencies: {deps}")
                if task.files:
                    lines.append(f"  - Files: {', '.join(task.files)}")
            lines.append("")

        return "\n".join(lines)

    def get_wave_summary(self) -> dict[str, Any]:
        """Return a serializable summary of the wave plan."""
        if not self.waves:
            self.build_waves()

        return {
            "total_waves": len(self.waves),
            "total_tasks": len(self.tasks),
            "waves": [
                {
                    "wave_number": w.wave_number,
                    "parallel": len(w.tasks) > 1,
                    "tasks": [
                        {"task_id": t.task_id, "name": t.name}
                        for t in w.tasks
                    ],
                }
                for w in self.waves
            ],
        }
