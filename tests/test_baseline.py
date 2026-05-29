from __future__ import annotations

import unittest

from event_graph_dev.baseline import load_baseline_summary


class BaselineTest(unittest.TestCase):
    def test_main_system_baseline_is_readable(self) -> None:
        summary = load_baseline_summary()

        self.assertGreaterEqual(summary.active_project_count, 100)
        self.assertGreaterEqual(summary.knowledge_point_count, 100)
        self.assertGreaterEqual(summary.graph_edge_count, 100)
        self.assertGreaterEqual(summary.plugin_project_count, 100)
        self.assertIn("L2", summary.project_count_by_age_band)
        self.assertIn("supports_project", summary.graph_edge_count_by_relation)


if __name__ == "__main__":
    unittest.main()
