"""
Metrics and Feedback System
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class ProjectMetrics:
    """Metrics for a project"""

    project_name: str
    prp_generation_time_minutes: float = 0.0
    total_phase_generations: int = 0
    failed_phase_generations: int = 0
    phase_failure_rate: float = 0.0
    task_completion_rate: float = 0.0
    test_coverage_achieved: float = 0.0
    code_quality_score: float = 0.0
    rework_rate: float = 0.0
    total_tasks: int = 0
    completed_tasks: int = 0
    created_at: str = ""
    updated_at: str = ""
    # Category-specific rework tracking for Confidence Adjustment
    category_rework_rates: dict[str, dict[str, float]] = field(default_factory=dict)
    # Format: {"security": {"total": 10, "rework": 3, "rate": 0.3}, ...}

    # ROI Tracking: Token savings from Context Pruning
    tokens_saved: int = 0  # Total tokens saved via Context Pruning
    tokens_used: int = 0  # Total tokens used
    context_pruning_events: int = 0  # Number of times Context Pruning was applied
    estimated_cost_saved_usd: float = 0.0  # Estimated cost savings (based on token pricing)
    tasks_with_commits: int = 0
    traceability_gaps: int = 0
    last_traceability_check: str = ""
    phase_generation_stats: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now(UTC).isoformat()


@dataclass
class Feedback:
    """Feedback on PRP quality"""

    prp_phase: str
    quality: str  # "high", "medium", "low"
    clarity: str
    completeness: str
    actionability: str
    comments: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


class MetricsCollector:
    """Collects and stores project metrics"""

    def __init__(self, metrics_dir: Path) -> None:
        """
        Initialize metrics collector

        Args:
            metrics_dir: Directory to store metrics files
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def record_project_start(self, project_name: str) -> ProjectMetrics:
        """
        Record project start

        Args:
            project_name: Name of the project

        Returns:
            ProjectMetrics instance
        """
        metrics = ProjectMetrics(project_name=project_name)
        self.save_metrics(metrics)
        return metrics

    def record_prp_generation_time(self, project_name: str, duration_minutes: float) -> None:
        """
        Record PRP generation time

        Args:
            project_name: Name of the project
            duration_minutes: Time taken in minutes
        """
        metrics = self.load_metrics(project_name)
        metrics.prp_generation_time_minutes = duration_minutes
        metrics.updated_at = datetime.now(UTC).isoformat()
        self.save_metrics(metrics)

    def record_phase_generation(
        self,
        project_name: str,
        phase_id: str,
        duration_seconds: float,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        """
        Record metrics for an individual PRP phase generation.

        Args:
            project_name: Name of the project being generated
            phase_id: Identifier of the phase (e.g., F0, F1)
            duration_seconds: Time spent generating the phase
            success: Whether the generation succeeded
            error_message: Optional error message when success is False
        """
        metrics = self.load_metrics(project_name)
        stats = metrics.phase_generation_stats.setdefault(
            phase_id,
            {
                "runs": 0,
                "failures": 0,
                "total_time_seconds": 0.0,
                "avg_time_seconds": 0.0,
                "failure_rate": 0.0,
                "last_error": "",
            },
        )

        stats["runs"] += 1
        stats["total_time_seconds"] += duration_seconds
        stats["avg_time_seconds"] = stats["total_time_seconds"] / stats["runs"]

        if not success:
            stats["failures"] += 1
            stats["last_error"] = error_message or ""

        stats["failure_rate"] = stats["failures"] / stats["runs"]

        metrics.total_phase_generations += 1
        if not success:
            metrics.failed_phase_generations += 1

        if metrics.total_phase_generations > 0:
            metrics.phase_failure_rate = (
                metrics.failed_phase_generations / metrics.total_phase_generations
            ) * 100

        metrics.updated_at = datetime.now(UTC).isoformat()
        self.save_metrics(metrics)

    def record_task_completion(self, project_name: str, task_id: str, success: bool) -> None:
        """
        Record task completion

        Args:
            project_name: Name of the project
            task_id: Task ID
            success: Whether the task was completed successfully
        """
        metrics = self.load_metrics(project_name)
        metrics.completed_tasks += 1 if success else 0
        metrics.task_completion_rate = (metrics.completed_tasks / metrics.total_tasks * 100) if metrics.total_tasks > 0 else 0.0
        metrics.updated_at = datetime.now(UTC).isoformat()
        self.save_metrics(metrics)

    def record_test_coverage(self, project_name: str, coverage_percentage: float) -> None:
        """
        Record test coverage

        Args:
            project_name: Name of the project
            coverage_percentage: Test coverage percentage
        """
        metrics = self.load_metrics(project_name)
        metrics.test_coverage_achieved = coverage_percentage
        metrics.updated_at = datetime.now(UTC).isoformat()
        self.save_metrics(metrics)

    def record_code_quality(self, project_name: str, quality_score: float) -> None:
        """
        Record code quality score

        Args:
            project_name: Name of the project
            quality_score: Quality score (0-10)
        """
        metrics = self.load_metrics(project_name)
        metrics.code_quality_score = quality_score
        metrics.updated_at = datetime.now(UTC).isoformat()
        self.save_metrics(metrics)

    def record_rework(self, project_name: str, category: str, rework_required: bool) -> None:
        """
        Record rework for a specific category (for Confidence Adjustment)

        This enables ML-like local learning: if "security" tasks always result in 30% rework,
        the estimator will automatically inflate story points for future security tasks.

        Args:
            project_name: Name of the project
            category: Task category (e.g., "security", "authentication", "api")
            rework_required: Whether rework was needed
        """
        metrics = self.load_metrics(project_name)

        # Initialize category tracking if needed
        if category not in metrics.category_rework_rates:
            metrics.category_rework_rates[category] = {"total": 0, "rework": 0}

        # Update counts
        metrics.category_rework_rates[category]["total"] += 1
        if rework_required:
            metrics.category_rework_rates[category]["rework"] += 1

        # Calculate rate
        total = metrics.category_rework_rates[category]["total"]
        rework_count = metrics.category_rework_rates[category]["rework"]
        metrics.category_rework_rates[category]["rate"] = rework_count / total if total > 0 else 0.0

        metrics.updated_at = datetime.now(UTC).isoformat()
        self.save_metrics(metrics)

    def get_category_rework_rate(self, project_name: str, category: str) -> float:
        """
        Get rework rate for a specific category

        Args:
            project_name: Name of the project
            category: Task category

        Returns:
            Rework rate (0.0 to 1.0) for the category, or 0.0 if no data
        """
        metrics = self.load_metrics(project_name)
        if category in metrics.category_rework_rates:
            return metrics.category_rework_rates[category].get("rate", 0.0)
        return 0.0

    def save_metrics(self, metrics: ProjectMetrics) -> None:
        """Save metrics to file"""
        metrics_file = self.metrics_dir / f"{metrics.project_name}.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(asdict(metrics), f, indent=2, ensure_ascii=False)

    def record_traceability_status(self, project_name: str, tasks_with_commits: int, total_tasks: int) -> None:
        """
        Record inverse traceability status (Tasks → Commits/PRs)

        Args:
            project_name: Name of the project
            tasks_with_commits: Number of tasks mapped to commits
            total_tasks: Total number of analyzed tasks
        """
        metrics = self.load_metrics(project_name)
        metrics.tasks_with_commits = tasks_with_commits
        metrics.traceability_gaps = max(total_tasks - tasks_with_commits, 0)
        metrics.last_traceability_check = datetime.now(UTC).isoformat()
        metrics.updated_at = metrics.last_traceability_check
        self.save_metrics(metrics)

    def load_metrics(self, project_name: str) -> ProjectMetrics:
        """Load metrics from file"""
        metrics_file = self.metrics_dir / f"{project_name}.json"
        if metrics_file.exists():
            with open(metrics_file, encoding="utf-8") as f:
                data = json.load(f)
                # Ensure category_rework_rates is a dict if missing
                if "category_rework_rates" not in data:
                    data["category_rework_rates"] = {}
                if "phase_generation_stats" not in data:
                    data["phase_generation_stats"] = {}
                data.setdefault("total_phase_generations", 0)
                data.setdefault("failed_phase_generations", 0)
                data.setdefault("phase_failure_rate", 0.0)
                return ProjectMetrics(**data)
        return ProjectMetrics(project_name=project_name)

    def save_feedback(self, feedback: Feedback) -> None:
        """Save feedback to file"""
        feedback_file = self.metrics_dir / f"feedback_{feedback.prp_phase}.json"
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(asdict(feedback), f, indent=2, ensure_ascii=False)

    def get_all_metrics(self) -> list[ProjectMetrics]:
        """Get all project metrics"""
        metrics = []
        for metrics_file in self.metrics_dir.glob("*.json"):
            if metrics_file.name.startswith("feedback_"):
                continue
            try:
                with open(metrics_file, encoding="utf-8") as f:
                    data = json.load(f)
                    metrics.append(ProjectMetrics(**data))
            except Exception:
                continue
        return metrics

    def get_average_metrics(self) -> dict[str, Any]:
        """Get average metrics across all projects"""
        all_metrics = self.get_all_metrics()
        if not all_metrics:
            return {}

        return {
            "avg_prp_generation_time": sum(m.prp_generation_time_minutes for m in all_metrics)
            / len(all_metrics),
            "avg_task_completion_rate": sum(m.task_completion_rate for m in all_metrics)
            / len(all_metrics),
            "avg_test_coverage": sum(m.test_coverage_achieved for m in all_metrics)
            / len(all_metrics),
            "avg_code_quality": sum(m.code_quality_score for m in all_metrics) / len(all_metrics),
            "total_projects": len(all_metrics),
        }

    def record_context_pruning(self, project_name: str, tokens_saved: int, cost_saved: float, tokens_used: int = 0) -> None:
        """
        Record Context Pruning event for ROI tracking

        Estimates cost savings based on token usage. Assumes:
        - Input tokens: $0.03 per 1K tokens (GPT-4 pricing)
        - Output tokens: $0.06 per 1K tokens
        - Average ratio: 70% input, 30% output

        Args:
            project_name: Name of the project
            tokens_saved: Number of tokens saved via Context Pruning
            cost_saved: Estimated cost saved in USD
            tokens_used: Total tokens used in the operation (optional)
        """
        metrics = self.load_metrics(project_name)

        metrics.tokens_saved += tokens_saved
        if tokens_used > 0:
            metrics.tokens_used += tokens_used
        metrics.context_pruning_events += 1

        # Estimate cost savings (simplified calculation)
        # Using average pricing: $0.03 per 1K input tokens, $0.06 per 1K output tokens
        # Assuming 70% input, 30% output ratio
        input_tokens_saved = int(tokens_saved * 0.7)
        output_tokens_saved = int(tokens_saved * 0.3)

        cost_saved = (input_tokens_saved / 1000 * 0.03) + (output_tokens_saved / 1000 * 0.06)
        metrics.estimated_cost_saved_usd += cost_saved

        metrics.updated_at = datetime.now(UTC).isoformat()
        self.save_metrics(metrics)

    def get_roi_metrics(self, project_name: str) -> dict:
        """
        Get ROI metrics for a project

        Returns:
            Dictionary with ROI information including token savings and cost estimates
        """
        metrics = self.load_metrics(project_name)

        if metrics.tokens_used == 0:
            return {
                "tokens_saved": 0,
                "tokens_used": 0,
                "savings_percentage": 0.0,
                "estimated_cost_saved_usd": 0.0,
                "context_pruning_events": 0,
            }

        savings_percentage = (
            (metrics.tokens_saved / metrics.tokens_used * 100) if metrics.tokens_used > 0 else 0.0
        )

        return {
            "tokens_saved": metrics.tokens_saved,
            "tokens_used": metrics.tokens_used,
            "savings_percentage": savings_percentage,
            "estimated_cost_saved_usd": metrics.estimated_cost_saved_usd,
            "context_pruning_events": metrics.context_pruning_events,
        }
