from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from event_graph_dev.git_preflight import inspect_main_system_git_preflight


class GitPreflightTest(unittest.TestCase):
    def test_reports_missing_git_repository_and_risky_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "backend").mkdir()
            (root / "backend" / ".env").write_text("SECRET=1\n", encoding="utf-8")
            (root / "data").mkdir()
            (root / "data" / "vsle_growth_map.db").write_text("db", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "backend" / "__pycache__").mkdir()

            result = inspect_main_system_git_preflight(root)

        self.assertFalse(result.is_git_repository)
        self.assertFalse(result.has_remote)
        self.assertIn("main_system_not_git_repository", result.blockers)
        self.assertIn("remote_not_configured", result.blockers)
        self.assertIn("backend/.env", result.risky_paths)
        self.assertIn("data/vsle_growth_map.db", result.risky_paths)
        self.assertIn("node_modules", result.risky_paths)
        self.assertIn("backend/__pycache__", result.risky_paths)

    def test_detects_git_repository_and_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "remote", "add", "origin", "https://github.com/example/main-system.git"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )

            result = inspect_main_system_git_preflight(root)

        self.assertTrue(result.is_git_repository)
        self.assertTrue(result.has_remote)
        self.assertEqual(result.remotes["origin"], "https://github.com/example/main-system.git")
        self.assertNotIn("main_system_not_git_repository", result.blockers)
        self.assertNotIn("remote_not_configured", result.blockers)


if __name__ == "__main__":
    unittest.main()
