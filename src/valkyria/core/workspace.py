"""
Workspace detection and scoped file discovery.

Detection order from cwd upward:
1. Nearest directory containing a `.valkyrie` marker
2. Nearest directory containing a `.git` directory/file
3. Fallback to the launch directory itself
"""

from __future__ import annotations

import os
from pathlib import Path

_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".eggs",
}


def detect_workspace_root(start_dir: Path | None = None) -> Path:
    """Detect the workspace root starting from start_dir (defaults to cwd)."""
    start = (start_dir or Path.cwd()).resolve()
    candidates = [start, *start.parents]

    for directory in candidates:
        if (directory / ".valkyrie").exists():
            return directory

    for directory in candidates:
        if (directory / ".git").exists():
            return directory

    return start


def resolve_workspace_path(workspace_root: Path, raw_path: str) -> Path | None:
    """
    Resolve a path relative to workspace_root, rejecting escapes outside the root.

    Returns the resolved Path if inside workspace_root, or None if invalid/outside.
    """
    root = workspace_root.resolve()
    cleaned = raw_path.strip()
    if not cleaned:
        return None
    target = Path(cleaned)
    candidate = target.resolve() if target.is_absolute() else (root / target).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def list_workspace_files(workspace_root: Path, *, max_files: int = 2000) -> list[str]:
    """
    Return sorted relative POSIX paths inside workspace_root, skipping ignored dirs.
    """
    root = workspace_root.resolve()
    if not root.exists():
        return []

    results: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in _IGNORED_DIRS and not d.endswith(".egg-info")
        )
        rel_dir = Path(dirpath).relative_to(root)
        for fname in sorted(filenames):
            rel_path = (rel_dir / fname).as_posix() if str(rel_dir) != "." else fname
            results.append(rel_path)
            if len(results) >= max_files:
                return results
    return results

