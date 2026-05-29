from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from event_graph_dev.models import PositioningResult, TeacherIdea
from event_graph_dev.planner import position_teacher_idea


REQUIRED_PACKAGE_FILES = (
    "project.json",
    "curriculum.md",
    "lesson_plan.json",
    "knowledge_map.json",
    "materials.json",
    "assessment.json",
    "ai_guardrails.json",
    "zongping_map.json",
    "competition_map.json",
    "parent_view.md",
    "teacher_notes.md",
    "README.md",
)

REQUIRED_PROJECT_FIELDS = (
    "project_id",
    "package_id",
    "name",
    "version",
    "status",
    "lifecycle_stage",
    "age_band",
    "age_range",
    "course_series",
    "duration_hours",
    "difficulty_range",
    "project_maturity_level",
    "knowledge_point_ids",
    "ai_competency_ids",
    "hardware_stack",
    "software_stack",
    "evidence_outputs",
    "rag_indexable",
    "recommendable",
)

SEVEN_DIMENSIONS = (
    "问题定义",
    "逻辑建模",
    "AI协作",
    "代码/硬件实现",
    "数据与证据",
    "迭代改进",
    "交付表达",
)

AGE_RANGES = {
    "L1": "3-6",
    "L2": "7-9",
    "L3": "10-12",
    "L4": "13-15",
    "L5": "16-18",
}

AI_ASSIST_LIMITS = {
    "L1": "0%，仅允许教师端演示和备课辅助",
    "L2": "不超过50%",
    "L3": "不超过30%",
    "L4": "不超过20%",
    "L5": "不超过10%",
}


@dataclass(frozen=True)
class ProjectDraft:
    idea_id: str
    status: str
    files: tuple[str, ...]
    positioning: PositioningResult
    project_manifest: dict[str, Any]
    package_files: dict[str, Any]
    validation_preview: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "idea_id": self.idea_id,
            "status": self.status,
            "files": list(self.files),
            "positioning": self.positioning.to_dict(),
            "project_manifest": self.project_manifest,
            "package_files": self.package_files,
            "validation_preview": self.validation_preview,
        }


@dataclass(frozen=True)
class DraftExportResult:
    package_dir: Path
    manifest_path: Path
    export_manifest_path: Path
    status: str
    files: tuple[str, ...]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "idea"


def _difficulty_range(age_band: str) -> list[int]:
    return {
        "L1": [1, 3],
        "L2": [2, 5],
        "L3": [3, 6],
        "L4": [5, 8],
        "L5": [6, 10],
    }.get(age_band, [3, 6])


def _unique(values: tuple[str, ...] | list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in values if item))


def _default_title(idea: TeacherIdea, positioning: PositioningResult) -> str:
    if positioning.candidate_existing_project_keywords:
        return f"{positioning.candidate_existing_project_keywords[0]}变体项目"
    return idea.idea_text[:24] or "事理图谱生成项目草案"


def _build_manifest(idea_id: str, idea: TeacherIdea, positioning: PositioningResult, title: str) -> dict[str, Any]:
    age_band = positioning.stage_decision.age_band
    target_competitions: list[str] = []
    if age_band != "L1" and idea.target_use == "competition":
        target_competitions.append("待按当年规则确认的竞赛方向")

    return {
        "project_id": f"EG-{age_band}-{_slug(idea_id).upper()}",
        "package_id": f"pkg-event-graph-{_slug(idea_id)}",
        "name": title,
        "version": "0.1.0",
        "status": "draft",
        "lifecycle_stage": "draft",
        "age_band": age_band,
        "age_range": AGE_RANGES.get(age_band, "10-12"),
        "course_series": "EVENT_GRAPH_GENERATED",
        "course_track": ["事理图谱", positioning.stage_decision.slot_type, positioning.generation_recommendation.mode],
        "duration_hours": idea.duration_hours or 8,
        "difficulty_range": _difficulty_range(age_band),
        "project_maturity_level": "draft",
        "target_exams": [],
        "target_competitions": target_competitions,
        "recommended_exams": [],
        "recommended_competitions": target_competitions,
        "knowledge_point_ids": list(positioning.knowledge_chain.core),
        "ai_competency_ids": [item for item in positioning.knowledge_chain.core if "AI" in item or "ai" in item.lower()],
        "hardware_stack": list(idea.available_hardware) or ["待教师确认的课堂器材"],
        "software_stack": ["Scratch/图形化编程或同阶段工具", "教师确认后补齐"],
        "evidence_outputs": ["项目草图", "调试记录", "学生讲解卡", "课堂展示材料"],
        "zongping_categories": [] if age_band in {"L1", "L2"} else ["研究性学习", "科技创新活动"],
        "competition_categories": target_competitions,
        "rag_indexable": False,
        "recommendable": False,
        "alignment_quality_status": "draft_pending_review",
        "alignment_generated_by": "event_graph_dev",
        "source_idea_id": idea_id,
        "source_idea_text": idea.idea_text,
        "insert_slot_type": positioning.stage_decision.slot_type,
        "generation_mode": positioning.generation_recommendation.mode,
        "ai_assist_limit": AI_ASSIST_LIMITS.get(age_band, "按阶段控制"),
        "review_required": True,
    }


def _build_package_files(manifest: dict[str, Any], idea: TeacherIdea, positioning: PositioningResult) -> dict[str, Any]:
    title = str(manifest["name"])
    required_review = _unique(("teacher_review", *positioning.generation_recommendation.required_review))
    return {
        "project.json": manifest,
        "curriculum.md": (
            f"# {title}\n\n"
            f"教师思路：{idea.idea_text}\n\n"
            f"插入阶段：{positioning.stage_decision.slot_type}。\n\n"
            "本草案只提供 ProjectPackage 文件骨架，必须经过教师确认和教研审核后才能进入项目插件审核流程。"
        ),
        "lesson_plan.json": {
            "lessons": [
                {"stage": "问题定义", "focus": "学生先描述任务、约束和成功标准。"},
                {"stage": "方案设计", "focus": "连接前置知识、核心知识和可观察证据。"},
                {"stage": "实现调试", "focus": "保留失败记录、调试过程和学生解释。"},
                {"stage": "展示复盘", "focus": "形成讲解卡、家长视角和后续挑战。"},
            ],
            "teacher_confirmation_required": True,
        },
        "knowledge_map.json": {
            "prerequisite_knowledge_point_ids": list(positioning.knowledge_chain.before),
            "core_knowledge_point_ids": list(positioning.knowledge_chain.core),
            "extension_knowledge_point_ids": list(positioning.knowledge_chain.after),
            "candidate_existing_project_keywords": list(positioning.candidate_existing_project_keywords),
        },
        "materials.json": {
            "hardware": manifest["hardware_stack"],
            "software": manifest["software_stack"],
            "safety": ["用电安全", "器材边界确认", "学生隐私保护"],
            "to_be_confirmed": ["班级设备数量", "课时长度", "教师可接受的AI辅助比例"],
        },
        "assessment.json": {
            "dimensions": [
                {"dimension": dimension, "levels": ["待补齐", "达标", "优秀"], "evidence": "课堂作品与过程记录"}
                for dimension in SEVEN_DIMENSIONS
            ]
        },
        "ai_guardrails.json": {
            "ai_capabilities": ["生成启发问题", "辅助教师备课", "提供调试建议"],
            "student_obligatory_tasks": ["亲自完成问题描述", "亲自完成核心搭建/代码/调试", "亲自解释作品"],
            "ai_output_validation": ["学生必须复述AI建议并说明取舍", "教师抽查关键步骤"],
            "anti_cognitive_offloading": ["先学生草稿，再AI建议，再学生修改", "AI不得直接替代最终作品"],
            "AI使用边界": [manifest["ai_assist_limit"], "不生成可直接复制的完整代码"],
            "防认知卸载机制": ["解释门", "过程证据保留", "教师确认后再进入审核"],
        },
        "zongping_map.json": {
            "categories": manifest["zongping_categories"],
            "materials": manifest["evidence_outputs"],
            "review_note": "综评映射需教研审核后固化。",
        },
        "competition_map.json": {
            "competitions": manifest["target_competitions"],
            "fit_basis": "L1只作为前置能力和展示项目；L2+需按当年竞赛规则复核。",
            "risk_tips": ["不得直接包装课堂项目为竞赛项目", "不得跳过教研审核"],
        },
        "parent_view.md": f"{title} 会让学生围绕真实问题完成可讲、可演示、可复盘的作品。",
        "teacher_notes.md": "\n".join(required_review),
        "README.md": "本目录由事理图谱原型导出，状态固定为 draft，需通过 ProjectPackage 审核后才能入库。",
    }


def generate_project_draft(idea_id: str, idea: TeacherIdea, draft_title: str | None = None) -> ProjectDraft:
    positioning = position_teacher_idea(idea)
    title = draft_title or _default_title(idea, positioning)
    manifest = _build_manifest(idea_id, idea, positioning, title)
    package_files = _build_package_files(manifest, idea, positioning)
    required_review = _unique(("teacher_review", *positioning.generation_recommendation.required_review, "project_package_validation"))
    if "teaching_research_review" not in required_review:
        required_review.append("teaching_research_review")
    validation_preview = {
        "can_activate": False,
        "required_review": required_review,
        "missing_files": [filename for filename in REQUIRED_PACKAGE_FILES if filename not in package_files],
        "risk_flags": list(positioning.risk_flags),
        "reason": "项目草案必须先通过教师确认、教研审核和项目插件校验，不能直接 active。",
    }
    return ProjectDraft(
        idea_id=idea_id,
        status="draft",
        files=REQUIRED_PACKAGE_FILES,
        positioning=positioning,
        project_manifest=manifest,
        package_files=package_files,
        validation_preview=validation_preview,
    )


def _write_payload(path: Path, payload: Any) -> None:
    if path.suffix == ".json":
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        path.write_text(str(payload), encoding="utf-8")


def export_project_draft(draft: ProjectDraft, output_root: Path, overwrite: bool = False) -> DraftExportResult:
    package_id = str(draft.project_manifest["package_id"])
    package_dir = output_root / package_id
    if package_dir.exists() and not overwrite:
        raise FileExistsError(f"Draft package already exists: {package_dir}")
    package_dir.mkdir(parents=True, exist_ok=True)

    for filename in REQUIRED_PACKAGE_FILES:
        _write_payload(package_dir / filename, draft.package_files[filename])

    export_manifest = {
        "idea_id": draft.idea_id,
        "package_id": package_id,
        "project_id": draft.project_manifest["project_id"],
        "status": draft.status,
        "files": list(draft.files),
        "status_flow": ["draft", "in_review", "approved", "active"],
        "positioning": draft.positioning.to_dict(),
        "validation_preview": draft.validation_preview,
    }
    export_manifest_path = package_dir / "event_graph_export.json"
    _write_payload(export_manifest_path, export_manifest)
    return DraftExportResult(
        package_dir=package_dir,
        manifest_path=package_dir / "project.json",
        export_manifest_path=export_manifest_path,
        status=draft.status,
        files=draft.files,
    )
