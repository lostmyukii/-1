from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from event_graph_dev import TeacherIdea
from event_graph_dev.draft import REQUIRED_PACKAGE_FILES, REQUIRED_PROJECT_FIELDS, export_project_draft, generate_project_draft


class DraftExportTest(unittest.TestCase):
    def test_export_project_draft_writes_complete_draft_package(self) -> None:
        draft = generate_project_draft(
            "IDEA-VOICE-CAR-L2",
            TeacherIdea(
                idea_text="我想让孩子做一个用语音控制小车给同学送物资的项目",
                age=8,
                available_hardware=("Arduino", "语音模块", "小车底盘"),
                duration_hours=8,
            ),
            draft_title="语音送货小车项目",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_project_draft(draft, Path(tmpdir))

            self.assertEqual(result.status, "draft")
            self.assertEqual(set(result.files), set(REQUIRED_PACKAGE_FILES))
            for filename in REQUIRED_PACKAGE_FILES:
                self.assertTrue((result.package_dir / filename).exists(), filename)

            manifest = json.loads((result.package_dir / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "draft")
            self.assertEqual(manifest["lifecycle_stage"], "draft")
            self.assertFalse(manifest["rag_indexable"])
            self.assertFalse(manifest["recommendable"])
            for field in REQUIRED_PROJECT_FIELDS:
                self.assertIn(field, manifest)

            export_manifest = json.loads((result.package_dir / "event_graph_export.json").read_text(encoding="utf-8"))
            self.assertFalse(export_manifest["validation_preview"]["can_activate"])
            self.assertIn("project_package_validation", export_manifest["validation_preview"]["required_review"])
            self.assertEqual(export_manifest["status_flow"], ["draft", "in_review", "approved", "active"])

    def test_l1_competition_draft_export_keeps_competition_empty(self) -> None:
        draft = generate_project_draft(
            "IDEA-L1-COMPETITION",
            TeacherIdea(
                idea_text="幼儿园孩子想参加机器人竞赛，做一个自动完成任务的小车",
                age=5,
                target_use="competition",
            ),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_project_draft(draft, Path(tmpdir))
            manifest = json.loads((result.package_dir / "project.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["age_band"], "L1")
        self.assertEqual(manifest["target_competitions"], [])
        self.assertIn("age_risk", draft.positioning.risk_flags)
        self.assertIn("teacher_review", draft.validation_preview["required_review"])


if __name__ == "__main__":
    unittest.main()
