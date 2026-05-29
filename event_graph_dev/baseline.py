from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MAIN_ROOT = Path("/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级")
DEFAULT_DB_PATH = DEFAULT_MAIN_ROOT / "data" / "vsle_growth_map.db"
DEFAULT_PROJECT_JSON = DEFAULT_MAIN_ROOT / "data" / "project_plugins" / "wsl_160_projects.json"


@dataclass(frozen=True)
class BaselineSummary:
    db_path: str
    project_json_path: str
    active_project_count: int
    knowledge_point_count: int
    graph_edge_count: int
    project_count_by_age_band: dict[str, int]
    graph_edge_count_by_relation: dict[str, int]
    plugin_project_count: int
    plugin_project_count_by_age_band: dict[str, int]


def _query_one_int(db: sqlite3.Connection, sql: str) -> int:
    value = db.execute(sql).fetchone()
    return int(value[0]) if value else 0


def _query_counts(db: sqlite3.Connection, sql: str) -> dict[str, int]:
    return {str(key): int(count) for key, count in db.execute(sql).fetchall()}


def _plugin_counts(project_json_path: Path) -> tuple[int, dict[str, int]]:
    if not project_json_path.exists():
        return 0, {}
    payload = json.loads(project_json_path.read_text(encoding="utf-8"))
    projects = payload.get("projects", []) if isinstance(payload, dict) else []
    counts: dict[str, int] = {}
    for project in projects:
        age_band = str(project.get("age_band") or "unknown")
        counts[age_band] = counts.get(age_band, 0) + 1
    return len(projects), dict(sorted(counts.items()))


def load_baseline_summary(
    db_path: Path = DEFAULT_DB_PATH,
    project_json_path: Path = DEFAULT_PROJECT_JSON,
) -> BaselineSummary:
    if not db_path.exists():
        raise FileNotFoundError(f"Main system database not found: {db_path}")

    with sqlite3.connect(db_path) as db:
        active_project_count = _query_one_int(db, "select count(*) from projects where deprecated=0")
        knowledge_point_count = _query_one_int(db, "select count(*) from knowledge_points")
        graph_edge_count = _query_one_int(db, "select count(*) from graph_edges")
        project_count_by_age_band = _query_counts(
            db,
            """
            select age_band, count(*)
            from projects
            where deprecated=0
            group by age_band
            order by age_band
            """,
        )
        graph_edge_count_by_relation = _query_counts(
            db,
            """
            select relation_type, count(*)
            from graph_edges
            group by relation_type
            order by count(*) desc, relation_type
            """,
        )

    plugin_project_count, plugin_project_count_by_age_band = _plugin_counts(project_json_path)
    return BaselineSummary(
        db_path=str(db_path),
        project_json_path=str(project_json_path),
        active_project_count=active_project_count,
        knowledge_point_count=knowledge_point_count,
        graph_edge_count=graph_edge_count,
        project_count_by_age_band=project_count_by_age_band,
        graph_edge_count_by_relation=graph_edge_count_by_relation,
        plugin_project_count=plugin_project_count,
        plugin_project_count_by_age_band=plugin_project_count_by_age_band,
    )
