"""Local event-graph prototype package."""

from event_graph_dev.baseline import BaselineSummary, load_baseline_summary
from event_graph_dev.draft import DraftExportResult, ProjectDraft, export_project_draft, generate_project_draft
from event_graph_dev.models import (
    GenerationRecommendation,
    InsertionSlot,
    KnowledgeChain,
    PositioningResult,
    StageDecision,
    TeacherIdea,
)
from event_graph_dev.planner import position_teacher_idea

__all__ = [
    "BaselineSummary",
    "DraftExportResult",
    "GenerationRecommendation",
    "InsertionSlot",
    "KnowledgeChain",
    "PositioningResult",
    "ProjectDraft",
    "StageDecision",
    "TeacherIdea",
    "export_project_draft",
    "generate_project_draft",
    "load_baseline_summary",
    "position_teacher_idea",
]
