"""
Type definitions for Context Engineer
Provides TypedDict classes for better type safety and IDE support
"""

from typing import NotRequired, TypedDict


class ProjectInitResult(TypedDict):
    """Result of project initialization"""

    success: bool
    created_directories: list[str]
    created_files: list[str]
    generated_files: list[str]
    stack_structure_created: bool


class PRDGenerationResult(TypedDict):
    """Result of PRD generation"""

    success: bool
    prd_file: str
    prd_structured: str


class PRPGenerationResult(TypedDict):
    """Result of PRP generation"""

    success: bool
    phases: list[str]
    prd_used: str


class TaskGenerationResult(TypedDict):
    """Result of task generation"""

    success: bool
    tasks: list[str]
    tasks_dir: str


class DependencyCheckResult(TypedDict):
    """Result of dependency check"""

    valid: bool
    errors: list[str]


class ValidationResult(TypedDict):
    """Result of validation operation"""

    valid: bool
    errors: list[str]
    warnings: list[str]
    error_count: int
    warning_count: int


class TraceabilityResult(TypedDict):
    """Result of traceability validation"""

    valid: bool
    errors: list[str]
    warnings: list[str]
    missing_tasks: list[str]
    orphaned_tasks: list[str]


class ContractValidationResult(TypedDict):
    """Result of contract validation"""

    success: bool
    errors: list[str]
    warnings: list[str]
    broken_contracts: list[str]


class MockServerResult(TypedDict):
    """Result of mock server generation"""

    success: bool
    errors: list[str]
    warnings: list[str]
    mock_url: str | None
    process_id: NotRequired[int]
    command: str
    message: NotRequired[str]


class PatternMetadata(TypedDict):
    """Metadata for code patterns"""

    name: str
    category: str
    complexity: str
    stack: list[str]
    requirements: list[str]
    description: NotRequired[str]


class ContextDict(TypedDict):
    """Context dictionary for pattern search"""

    stack: str | list[str]
    category: NotRequired[str]
    requirements: NotRequired[str | list[str]]
    description: NotRequired[str]
    metadata: NotRequired[PatternMetadata]


class MetricsDict(TypedDict):
    """Project metrics dictionary"""

    project_name: str
    prp_generation_time_minutes: float
    total_phase_generations: int
    failed_phase_generations: int
    phase_failure_rate: float
    task_completion_rate: float
    test_coverage_achieved: float
    code_quality_score: float
    rework_rate: float
    total_tasks: int
    completed_tasks: int
    created_at: str
    updated_at: str
    category_rework_rates: dict[str, dict[str, float]]
    tokens_saved: int
    tokens_used: int
    context_pruning_events: int
    estimated_cost_saved_usd: float
    tasks_with_commits: int
    traceability_gaps: int
    last_traceability_check: str
    phase_generation_stats: dict[str, dict[str, float]]


class ROIMetrics(TypedDict):
    """ROI metrics for context pruning"""

    tokens_saved: int
    cost_saved: float
    time_saved_seconds: float


class ConfigDict(TypedDict, total=False):
    """Project configuration dictionary"""

    project_name: str
    stack: str
    use_transformers: NotRequired[bool]
    embedding_model: NotRequired[str]
    created_at: NotRequired[str]
    version: NotRequired[str]


class StackFlags(TypedDict, total=False):
    """Stack feature flags"""

    is_python: bool
    is_node: bool
    is_go: bool
    is_vue: bool
    has_api: bool
    has_frontend: bool


class StackCommands(TypedDict, total=False):
    """Stack-specific commands"""

    init: NotRequired[str]
    install: NotRequired[str]
    dev: NotRequired[str]
    build: NotRequired[str]
    test: NotRequired[str]
    lint: NotRequired[str]


class AIGovernanceStatus(TypedDict):
    """AI governance status information"""

    transformers_available: bool
    current_model: str | None
    mode: str
    dependencies_ready: bool
    requires_installation: bool


class CompressedContext(TypedDict):
    """Compressed context mapping"""

    file_path: str
    compressed_content: str
    original_size: int
    compressed_size: int
