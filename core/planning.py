"""
Planning Module for Automated Effort Estimation
Automatically estimates story points based on historical data and complexity
"""

from dataclasses import dataclass

from .metrics import MetricsCollector


@dataclass
class TaskComplexity:
    """Represents task complexity metrics"""

    artifacts_count: int
    steps_count: int
    gherkin_scenarios_count: int
    dependencies_count: int
    stack_complexity: float  # 0.0 to 1.0 based on stack
    category_complexity: float  # 0.0 to 1.0 based on pattern category


class EffortEstimator:
    """Estimates effort points (story points) for tasks"""

    def __init__(self, metrics_collector: MetricsCollector):
        """
        Initialize effort estimator

        Args:
            metrics_collector: MetricsCollector instance for historical data
        """
        self.metrics = metrics_collector

    def calculate_complexity(self, task: dict, stack: str = "python-fastapi") -> TaskComplexity:
        """
        Calculate task complexity metrics

        Args:
            task: Task dictionary
            stack: Technology stack

        Returns:
            TaskComplexity instance
        """
        artifacts = task.get("artifacts", [])
        steps = task.get("steps", [])
        gherkin_scenarios = task.get("gherkin_scenarios", [])
        dependencies = task.get("dependencies", [])

        # Stack complexity factors (lower = simpler)
        stack_complexity_map = {
            "python-fastapi": 0.3,  # Simple, well-documented
            "node-react": 0.4,  # Moderate complexity
            "vue3": 0.4,  # Moderate complexity, similar to React
            "java-spring": 0.6,  # More verbose
            "go-gin": 0.3,  # Simple but less common patterns
            "rust-axum": 0.7,  # High complexity
        }
        stack_complexity = stack_complexity_map.get(stack, 0.5)

        # Category complexity (based on pattern category if available)
        category = task.get("metadata", {}).get("category", "general")
        category_complexity_map = {
            "authentication": 0.6,
            "data-models": 0.4,
            "api-patterns": 0.5,
            "ui-components": 0.5,
            "general": 0.5,
        }
        category_complexity = category_complexity_map.get(category, 0.5)

        return TaskComplexity(
            artifacts_count=len(artifacts),
            steps_count=len(steps),
            gherkin_scenarios_count=len(gherkin_scenarios),
            dependencies_count=len(dependencies),
            stack_complexity=stack_complexity,
            category_complexity=category_complexity,
        )

    def estimate_effort_points(self, task: dict, stack: str = "python-fastapi", project_name: str | None = None) -> int:
        """
        Estimate effort points for a task based on complexity and historical data

        Args:
            task: Task dictionary
            stack: Technology stack
            project_name: Optional project name for historical context

        Returns:
            Estimated effort points (story points)
        """
        complexity = self.calculate_complexity(task, stack)

        # Base effort calculation
        base_effort = 1  # Minimum 1 point

        # Add effort based on artifacts (files to create/modify)
        artifacts_effort = min(complexity.artifacts_count * 0.5, 3)

        # Add effort based on steps (implementation complexity)
        steps_effort = min(complexity.steps_count * 0.3, 2)

        # Add effort based on test scenarios (testing complexity)
        test_effort = min(complexity.gherkin_scenarios_count * 0.4, 2)

        # Add effort based on dependencies (integration complexity)
        deps_effort = min(complexity.dependencies_count * 0.5, 2)

        # Stack complexity multiplier
        stack_multiplier = 1.0 + complexity.stack_complexity

        # Category complexity multiplier
        category_multiplier = 1.0 + complexity.category_complexity

        # Calculate base points
        base_points = base_effort + artifacts_effort + steps_effort + test_effort + deps_effort

        # Apply multipliers
        estimated_points = int(base_points * stack_multiplier * category_multiplier)

        # Confidence Adjustment: Adjust based on historical data and category-specific rework
        confidence_adjustment = 1.0
        if project_name:
            # Get category from task metadata
            task_category = task.get("metadata", {}).get("category", task.get("category", ""))

            # Category-specific confidence adjustment (ML-like local learning)
            if task_category:
                category_adjustment = self._get_category_confidence_adjustment(project_name, task_category)
                confidence_adjustment *= category_adjustment

            # General historical adjustment
            historical_adjustment = self._get_historical_adjustment(project_name)
            confidence_adjustment *= historical_adjustment

        estimated_points = int(estimated_points * confidence_adjustment)

        return max(1, min(estimated_points, 13))

    def _get_category_confidence_adjustment(self, project_name: str, category: str) -> float:
        """
        Get confidence adjustment factor based on category-specific rework history

        Implements ML-like local learning: if a category (e.g., "security") always results
        in 30% rework, automatically inflate story points for future tasks of that category.

        Args:
            project_name: Project name
            category: Task category (e.g., "security", "authentication")

        Returns:
            Adjustment factor (1.0 = no adjustment, >1.0 = more effort needed)
        """
        try:
            category_rework_rate = self.metrics.get_category_rework_rate(project_name, category)

            # If category has high rework rate, inflate estimate
            if category_rework_rate > 0.3:  # >30% rework for this category
                return 1.3  # Inflate by 30%
            if category_rework_rate > 0.2:  # >20% rework
                return 1.2  # Inflate by 20%
            if category_rework_rate > 0.1:  # >10% rework
                return 1.1  # Inflate by 10%

            # If category has low rework rate, can slightly deflate
            if category_rework_rate < 0.05 and category_rework_rate > 0:  # <5% rework
                return 0.95  # Slightly deflate

            return 1.0
        except Exception:
            return 1.0

    def _get_historical_adjustment(self, project_name: str) -> float:
        """
        Get adjustment factor based on historical project metrics

        Args:
            project_name: Project name

        Returns:
            Adjustment factor (1.0 = no adjustment, >1.0 = more effort, <1.0 = less effort)
        """
        try:
            metrics = self.metrics.load_metrics(project_name)

            # If rework rate is high, tasks take longer
            if metrics.rework_rate > 0.2:  # >20% rework
                return 1.2

            # If completion rate is high, tasks are easier
            if metrics.task_completion_rate > 90:
                return 0.9

            # If average generation time is high, tasks are more complex
            if metrics.prp_generation_time_minutes > 30:
                return 1.1

            return 1.0
        except Exception:
            return 1.0

    def estimate_batch(
        self, tasks: list[dict], stack: str = "python-fastapi", project_name: str | None = None
    ) -> dict[str, int]:
        """
        Estimate effort for multiple tasks

        Args:
            tasks: List of task dictionaries
            stack: Technology stack
            project_name: Optional project name

        Returns:
            Dictionary mapping task_id to estimated points
        """
        estimates = {}
        for task in tasks:
            task_id = task.get("task_id", "unknown")
            estimates[task_id] = self.estimate_effort_points(task, stack, project_name)
        return estimates

    def get_complexity_breakdown(self, task: dict, stack: str = "python-fastapi") -> dict:
        """
        Get detailed complexity breakdown for a task

        Args:
            task: Task dictionary
            stack: Technology stack

        Returns:
            Dictionary with complexity breakdown
        """
        complexity = self.calculate_complexity(task, stack)
        estimated_points = self.estimate_effort_points(task, stack)

        return {
            "estimated_points": estimated_points,
            "complexity_metrics": {
                "artifacts": complexity.artifacts_count,
                "steps": complexity.steps_count,
                "test_scenarios": complexity.gherkin_scenarios_count,
                "dependencies": complexity.dependencies_count,
                "stack_complexity": complexity.stack_complexity,
                "category_complexity": complexity.category_complexity,
            },
            "breakdown": {
                "base": 1,
                "artifacts_contribution": min(complexity.artifacts_count * 0.5, 3),
                "steps_contribution": min(complexity.steps_count * 0.3, 2),
                "tests_contribution": min(complexity.gherkin_scenarios_count * 0.4, 2),
                "dependencies_contribution": min(complexity.dependencies_count * 0.5, 2),
            },
        }
