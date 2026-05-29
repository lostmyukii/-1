from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


RISKY_DIR_NAMES = {".git", "__pycache__", "node_modules"}
RISKY_FILE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}


@dataclass(frozen=True)
class GitPreflightResult:
    root_path: str
    is_git_repository: bool
    current_branch: str | None
    remotes: dict[str, str]
    risky_paths: tuple[str, ...]
    blockers: tuple[str, ...]

    @property
    def has_remote(self) -> bool:
        return bool(self.remotes)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["has_remote"] = self.has_remote
        return payload


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def _is_git_repository(root: Path) -> bool:
    result = _git(root, "rev-parse", "--is-inside-work-tree")
    return result.returncode == 0 and result.stdout.strip() == "true"


def _current_branch(root: Path) -> str | None:
    result = _git(root, "branch", "--show-current")
    branch = result.stdout.strip()
    return branch or None


def _remotes(root: Path) -> dict[str, str]:
    result = _git(root, "remote", "-v")
    remotes: dict[str, str] = {}
    if result.returncode != 0:
        return remotes
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[2] == "(fetch)":
            remotes[parts[0]] = parts[1]
    return remotes


def _is_risky_file(path: Path) -> bool:
    name = path.name
    if name == ".DS_Store":
        return True
    if name == ".env" or name.startswith(".env."):
        return True
    return path.suffix.lower() in RISKY_FILE_SUFFIXES


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def find_risky_paths(root: Path, limit: int = 200) -> tuple[str, ...]:
    risky: list[str] = []
    for current_root, dirs, files in os.walk(root):
        current = Path(current_root)
        for dirname in list(dirs):
            if dirname in RISKY_DIR_NAMES:
                risky.append(_relative(root, current / dirname))
                dirs.remove(dirname)
        for filename in files:
            file_path = current / filename
            if _is_risky_file(file_path):
                risky.append(_relative(root, file_path))
        if len(risky) >= limit:
            break
    return tuple(sorted(dict.fromkeys(risky))[:limit])


def inspect_main_system_git_preflight(root: Path | str) -> GitPreflightResult:
    root_path = Path(root)
    is_repo = _is_git_repository(root_path)
    remotes = _remotes(root_path) if is_repo else {}
    blockers: list[str] = []
    if not is_repo:
        blockers.append("main_system_not_git_repository")
    if not remotes:
        blockers.append("remote_not_configured")

    risky_paths = find_risky_paths(root_path)
    if risky_paths:
        blockers.append("risky_paths_need_gitignore_review")

    return GitPreflightResult(
        root_path=str(root_path),
        is_git_repository=is_repo,
        current_branch=_current_branch(root_path) if is_repo else None,
        remotes=remotes,
        risky_paths=risky_paths,
        blockers=tuple(blockers),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect main-system Git readiness without modifying files.")
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    result = inspect_main_system_git_preflight(args.root)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
