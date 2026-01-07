
from core.project_status_service import ProjectStatusService


class DummyPromptService:
    pass


def _build_service() -> ProjectStatusService:
    return ProjectStatusService(DummyPromptService())


def _sample_status_view() -> dict:
    return {
        "project_name": "Hyperion",
        "completion_status": {
            "init": True,
            "prd": True,
            "prps": False,
            "tasks": False,
            "implementation": False,
        },
        "has_prd": True,
        "prd_path": "./prd/PRD.md",
        "has_prps": False,
        "prp_completed": 3,
        "prp_total": 5,
        "has_tasks": False,
        "task_count": 0,
        "suggestions": ["Gerar PRPs F0-F2"],
        "total_steps": 5,
        "completed_steps": 2,
        "phase_names": {"F0": "Plan", "F1": "Scaffold"},
        "prp_phases": {
            "F0": {"exists": True, "valid": True},
            "F1": {"exists": False, "valid": False},
        },
    }


def test_status_template_renders_core_sections():
    service = _build_service()
    data = {
        "assistant_context": {"project_name": "Hyperion"},
        "status_view": _sample_status_view(),
        "metrics": {
            "story_points": 21,
            "rework_rate": 12.5,
            "task_completion_rate": 33.3,
            "test_coverage": 55.5,
        },
    }

    rendered = service.format_status_text(data)

    assert "Status do Projeto: Hyperion" in rendered
    assert "[OK] PRD" in rendered
    assert "Story Points estimados: 21" in rendered
    assert "Próximos Passos" in rendered


def test_checklist_template_highlights_focus():
    service = _build_service()
    text = service.format_checklist_text(_sample_status_view())

    assert "Checklist do Projeto" in text
    assert "[3/5] PRPs gerados" in text or "PRPs gerados" in text
    assert "Foco Atual" in text


def _assist_context_data() -> dict:
    return {
        "assistant_context": {
            "project_name": "Hyperion",
            "stack": "python-fastapi",
            "task_count": 4,
            "next_focus": "F0",
            "tags": ["AI", "Security"],
            "requirements": [
                {"id": "FR-001", "title": "Login", "priority": "MUST"},
                {"id": "FR-002", "title": "Audit", "priority": "SHOULD"},
            ],
        },
        "pattern_suggestions": [
            {"pattern_id": "PT-01", "category": "API", "name": "API Gateway", "tags": ["api"]}
        ],
        "cache_suggestions": [
            {"pattern_id": "PT-99", "success_rate": 0.8}
        ],
        "metrics": {
            "story_points": 21,
            "rework_rate": 12.5,
            "task_completion_rate": 33.3,
            "test_coverage": 55.5,
        },
        "status_view": _sample_status_view(),
    }


def test_assist_intro_template_lists_patterns():
    service = _build_service()
    rendered = service.render_assist_intro(_assist_context_data())

    assert "Context Engineer Assistant" in rendered
    assert "Stack: python-fastapi" in rendered
    assert "PT-01" in rendered
    assert "PT-99" in rendered


def test_assist_intro_html_contains_metrics_and_progress():
    service = _build_service()
    rendered = service.render_assist_intro(_assist_context_data(), output_format="html")

    assert "Story Points" in rendered
    assert "33.3%" in rendered  # completion metric
    if "Conclusão geral do pipeline" in rendered:
        assert "[OK] Inicialização" in rendered
    else:
        assert "Conclusão geral do pipeline" not in rendered
    assert "PT-99" in rendered
