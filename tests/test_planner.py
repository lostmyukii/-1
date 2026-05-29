from __future__ import annotations

import unittest

from event_graph_dev import TeacherIdea, position_teacher_idea


class PlannerTest(unittest.TestCase):
    def test_l2_voice_delivery_car_becomes_variant(self) -> None:
        result = position_teacher_idea(
            TeacherIdea(
                idea_text="我想让孩子做一个用语音控制小车给同学送物资的项目",
                age=8,
                available_hardware=("Arduino", "语音模块", "小车底盘"),
            )
        )

        self.assertEqual(result.stage_decision.age_band, "L2")
        self.assertEqual(result.stage_decision.slot_type, "synchronous_carrier")
        self.assertEqual(result.generation_recommendation.mode, "variant")
        self.assertIn("C2-L2-03 条件判断", result.knowledge_chain.core)
        self.assertIn("Arduino超声波避障小车", result.candidate_existing_project_keywords)

    def test_l1_competition_request_is_blocked_to_preremediation(self) -> None:
        result = position_teacher_idea(
            TeacherIdea(
                idea_text="想让幼儿园孩子用AI直接生成代码参加小车竞赛",
                age=5,
                target_use="competition",
            )
        )

        self.assertEqual(result.stage_decision.age_band, "L1")
        self.assertEqual(result.stage_decision.slot_type, "pre_remediation")
        self.assertIn("age_risk", result.risk_flags)
        self.assertEqual(result.generation_recommendation.mode, "reuse_existing")

    def test_l3_data_ai_idea_maps_to_system_design(self) -> None:
        result = position_teacher_idea(
            TeacherIdea(
                idea_text="做一个校园环境数据监测和AI分析项目",
                age_band="L3",
                available_hardware=("ESP32", "温湿度传感器"),
            )
        )

        self.assertEqual(result.stage_decision.age_band, "L3")
        self.assertIn("C3-L3-04 简单AI Agent", result.knowledge_chain.core)
        self.assertIn("校园物联网数据监测中心", result.candidate_existing_project_keywords)


if __name__ == "__main__":
    unittest.main()
