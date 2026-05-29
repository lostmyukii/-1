from __future__ import annotations

import re

from event_graph_dev.models import (
    GenerationRecommendation,
    InsertionSlot,
    KnowledgeChain,
    PositioningResult,
    StageDecision,
    TeacherIdea,
)


AGE_BANDS: tuple[tuple[str, int, int], ...] = (
    ("L1", 3, 6),
    ("L2", 7, 9),
    ("L3", 10, 12),
    ("L4", 13, 15),
    ("L5", 16, 18),
)


def infer_age_band(idea: TeacherIdea) -> str:
    if idea.age_band:
        return idea.age_band
    if idea.age is None:
        return "L3"
    for age_band, start, end in AGE_BANDS:
        if start <= idea.age <= end:
            return age_band
    if idea.age < 3:
        return "L1"
    return "L5"


def _has_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword.lower() in text.lower() for keyword in keywords)


def _normalize_terms(values: tuple[str, ...]) -> str:
    return " ".join(values).lower()


def build_knowledge_chain(idea: TeacherIdea, age_band: str) -> KnowledgeChain:
    text = idea.idea_text
    hardware_text = _normalize_terms(idea.available_hardware)
    has_car = _has_any(text + hardware_text, ("小车", "机器人", "车", "巡逻", "送货"))
    has_voice = _has_any(text, ("语音", "声音", "说话", "指令"))
    has_data = _has_any(text, ("数据", "统计", "图表", "分析", "监测"))
    has_ai = _has_any(text, ("AI", "人工智能", "识别", "模型", "视觉", "LLM", "RAG"))
    has_algorithm = _has_any(text, ("算法", "路径", "规划", "搜索", "排序", "图论", "动态规划"))

    if age_band == "L1":
        return KnowledgeChain(
            before=("具身感知", "安全操作", "简单模仿"),
            core=("因果关系", "序列指令", "表达复述"),
            after=("条件逻辑体验", "分类排序", "合作展示"),
        )
    if age_band == "L2" and has_car:
        core = ["C2-L2-02 事件驱动", "C2-L2-03 条件判断", "P2-L2-06 电机控制基础", "E2-L2-01 项目规划"]
        if has_voice:
            core.insert(1, "C2-L2-08 AI对话/语音辅助")
        return KnowledgeChain(
            before=("C1-L1-04 序列指令", "M2-L2-02 角度与方向"),
            core=tuple(core),
            after=("P2-L2-05 超声波测距", "E2-L2-03 测试调试", "C3-L3-02 函数与模块"),
        )
    if age_band == "L3" and (has_data or has_ai):
        return KnowledgeChain(
            before=("C3-L3-01 Python基础", "C3-L3-02 函数与模块"),
            core=("C3-L3-04 简单AI Agent", "M3-L3-04 数据统计", "E3-L3-01 系统设计"),
            after=("C4-L4-03 Edge AI部署", "E4-L4-04 技术报告", "E4-L4-05 Git协作"),
        )
    if age_band in {"L4", "L5"} and has_algorithm:
        return KnowledgeChain(
            before=("变量与数组", "函数模块化", "复杂度意识"),
            core=("C4-L4-01 C++算法基础", "M4-L4-01 复杂度分析", "E4-L4-01 竞赛策略"),
            after=("C5-L5-02 LLM应用开发", "E5-L5-04 科研报告", "系统架构设计"),
        )
    return KnowledgeChain(
        before=("当前阶段基础知识点",),
        core=("项目规划", "逻辑建模", "交付表达"),
        after=("迭代优化", "综合展示", "下一阶段衔接"),
    )


def decide_slot_type(idea: TeacherIdea, age_band: str) -> tuple[str, str]:
    if idea.target_use == "competition":
        if age_band == "L1":
            return "pre_remediation", "L1不直接进入竞赛路径，只做前置能力和课堂展示。"
        return "competition_packaging", "目标用途是竞赛，应优先生成竞赛包装和证据材料。"
    if idea.target_use in {"portfolio", "zongping"}:
        return "zongping_portfolio", "目标用途是作品集或综评，应强化证据、报告和展示材料。"
    if idea.known_knowledge_point_ids:
        return "extension_challenge", "已有知识点输入，适合作为延伸挑战或变体项目。"
    if age_band == "L1":
        return "pre_remediation", "L1适合作为具身体验和前置补齐，不直接生成学生端复杂项目。"
    return "synchronous_carrier", "教师思路可作为当前阶段核心知识点的项目载体。"


def candidate_project_keywords(idea: TeacherIdea, age_band: str) -> tuple[str, ...]:
    text = idea.idea_text
    candidates: list[str] = []
    if age_band == "L2" and _has_any(text, ("小车", "送货", "巡逻", "机器人")):
        candidates.extend(("Arduino超声波避障小车", "快递分拣机器人", "循线机器人挑战"))
    if _has_any(text, ("语音", "声音", "说话")):
        candidates.extend(("语音指令小车", "语音助手", "AI对话辅助"))
    if _has_any(text, ("数据", "统计", "图表", "分析")):
        candidates.extend(("智能数据侦探", "校园物联网数据监测中心", "数据侦探AI"))
    if _has_any(text, ("视觉", "识别", "图像", "手势")):
        candidates.extend(("AI视觉手势识别交互系统", "颜色魔法师", "表情识别相机"))
    if not candidates:
        candidates.append("同阶段项目库候选项目")
    return tuple(dict.fromkeys(candidates))


def generation_mode(idea: TeacherIdea, candidates: tuple[str, ...], risk_flags: tuple[str, ...]) -> GenerationRecommendation:
    text = idea.idea_text
    if "age_risk" in risk_flags:
        return GenerationRecommendation(
            mode="reuse_existing",
            reason="存在年龄或AI使用风险，先复用现有项目或生成教师端活动，不生成新项目包。",
            required_review=("teacher_review", "teaching_research_review"),
        )
    if len(candidates) >= 2 and not re.search(r"全新|没有|补一个|新增|新方向", text):
        return GenerationRecommendation(
            mode="variant",
            reason="已有相近项目，优先生成同ProjectSet下的场景变体，降低入库和实施风险。",
            required_review=("schema_validation", "teaching_research_review"),
        )
    return GenerationRecommendation(
        mode="new_package",
        reason="现有项目匹配不足，可生成新的ProjectPackage草案并进入审核。",
        required_review=("schema_validation", "knowledge_map_review", "ai_guardrail_review", "teaching_research_review"),
    )


def risk_flags_for(idea: TeacherIdea, age_band: str) -> tuple[str, ...]:
    flags: list[str] = []
    if age_band == "L1" and (idea.target_use == "competition" or _has_any(idea.idea_text, ("生成代码", "AI直接做", "自动完成"))):
        flags.append("age_risk")
    if not idea.available_hardware and _has_any(idea.idea_text, ("小车", "机器人", "传感器", "Arduino", "ESP32")):
        flags.append("hardware_unknown")
    if _has_any(idea.idea_text, ("完整代码", "直接生成程序", "自动写完")):
        flags.append("ai_overreliance_risk")
    return tuple(flags)


def position_teacher_idea(idea: TeacherIdea) -> PositioningResult:
    age_band = infer_age_band(idea)
    slot_type, reason = decide_slot_type(idea, age_band)
    knowledge_chain = build_knowledge_chain(idea, age_band)
    candidates = candidate_project_keywords(idea, age_band)
    risks = risk_flags_for(idea, age_band)
    confidence = 0.72
    if idea.age_band or idea.age is not None:
        confidence += 0.08
    if candidates and candidates[0] != "同阶段项目库候选项目":
        confidence += 0.08
    if risks:
        confidence -= 0.12
    confidence = max(0.35, min(0.95, round(confidence, 2)))

    slot = InsertionSlot(
        slot_type=slot_type,  # type: ignore[arg-type]
        position="after_current_or_before_next",
        anchor_project_keywords=candidates[:3],
        score=confidence,
        reason=reason,
    )
    recommendation = generation_mode(idea, candidates, risks)
    return PositioningResult(
        stage_decision=StageDecision(
            age_band=age_band,
            slot_type=slot_type,  # type: ignore[arg-type]
            confidence=confidence,
            reason=reason,
        ),
        knowledge_chain=knowledge_chain,
        insertion_slots=(slot,),
        candidate_existing_project_keywords=candidates,
        generation_recommendation=recommendation,
        risk_flags=risks,
    )
