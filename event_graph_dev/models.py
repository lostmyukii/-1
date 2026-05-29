from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


TargetUse = Literal["classroom", "parent_showcase", "competition", "portfolio", "zongping"]
GenerationMode = Literal["reuse_existing", "variant", "new_package"]
SlotType = Literal[
    "pre_remediation",
    "synchronous_carrier",
    "extension_challenge",
    "review_repair",
    "competition_packaging",
    "zongping_portfolio",
]


@dataclass(frozen=True)
class TeacherIdea:
    idea_text: str
    age: int | None = None
    age_band: str | None = None
    current_project_id: str | None = None
    known_knowledge_point_ids: tuple[str, ...] = ()
    available_hardware: tuple[str, ...] = ()
    duration_hours: int | None = None
    target_use: TargetUse = "classroom"
    teacher_constraints: tuple[str, ...] = ()


@dataclass(frozen=True)
class StageDecision:
    age_band: str
    slot_type: SlotType
    confidence: float
    reason: str


@dataclass(frozen=True)
class KnowledgeChain:
    before: tuple[str, ...] = ()
    core: tuple[str, ...] = ()
    after: tuple[str, ...] = ()


@dataclass(frozen=True)
class InsertionSlot:
    slot_type: SlotType
    position: str
    anchor_project_keywords: tuple[str, ...]
    score: float
    reason: str


@dataclass(frozen=True)
class GenerationRecommendation:
    mode: GenerationMode
    reason: str
    required_review: tuple[str, ...] = ()


@dataclass(frozen=True)
class PositioningResult:
    stage_decision: StageDecision
    knowledge_chain: KnowledgeChain
    insertion_slots: tuple[InsertionSlot, ...] = ()
    candidate_existing_project_keywords: tuple[str, ...] = ()
    generation_recommendation: GenerationRecommendation = field(
        default_factory=lambda: GenerationRecommendation(
            mode="reuse_existing",
            reason="默认优先复用现有项目。",
        )
    )
    risk_flags: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)
