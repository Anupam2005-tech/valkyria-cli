"""
Read-only workspace file access and indexable file collection.

All reads are strictly scoped to the detected workspace root.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from valkyria.core.workspace import list_workspace_files, resolve_workspace_path

if TYPE_CHECKING:
    from pathlib import Path

_MAX_READ_BYTES = 48_000
_MAX_INDEX_FILE_BYTES = 512_000

_BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".whl",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".bin",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".enc",
    ".pyc",
    ".pyo",
}


@dataclass
class FileReadResult:
    """Result of reading a workspace file."""

    path: Path
    rel_path: str
    content: str
    start_line: int
    end_line: int
    total_lines: int
    truncated: bool = False


def is_probably_binary(path: Path) -> bool:
    """Quickly detect binary files by extension or null-byte check."""
    if path.suffix.lower() in _BINARY_EXTENSIONS:
        return True
    try:
        sample = path.read_bytes()[:2048]
    except OSError:
        return True
    return b"\x00" in sample


def read_workspace_file(
    workspace_root: Path,
    raw_path: str,
    *,
    start_line: int = 1,
    end_line: int | None = None,
    max_bytes: int = _MAX_READ_BYTES,
) -> FileReadResult:
    """
    Safely read a text file inside workspace_root.

    Raises:
        PermissionError: If path escapes workspace_root.
        FileNotFoundError: If file doesn't exist or isn't a regular file.
        ValueError: If file appears to be binary or line bounds are invalid.
    """
    resolved = resolve_workspace_path(workspace_root, raw_path)
    if resolved is None:
        raise PermissionError(f"Path '{raw_path}' is outside workspace scope ({workspace_root}).")
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"File not found: {raw_path}")
    if is_probably_binary(resolved):
        raise ValueError(f"Cannot read binary file: {raw_path}")

    text = resolved.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    total_lines = len(lines)

    s = max(1, start_line)
    e = total_lines if end_line is None else min(total_lines, end_line)
    if s > max(1, total_lines):
        s = max(1, total_lines)
    if e < s:
        e = s

    selected = lines[s - 1 : e] if total_lines > 0 else []
    joined = "\n".join(selected)
    truncated = False
    if len(joined.encode("utf-8")) > max_bytes:
        joined = joined[:max_bytes] + "\n... [truncated]"
        truncated = True

    rel_path = resolved.relative_to(workspace_root.resolve()).as_posix()
    return FileReadResult(
        path=resolved,
        rel_path=rel_path,
        content=joined,
        start_line=s,
        end_line=e,
        total_lines=total_lines,
        truncated=truncated,
    )


def collect_indexable_files(
    workspace_root: Path,
    raw_target: str = ".",
) -> list[tuple[str, Path]]:
    """
    Collect readable text files under raw_target within workspace_root.

    Returns list of (relative_posix_path, absolute_path).
    """
    root = workspace_root.resolve()
    target = resolve_workspace_path(root, raw_target)
    if target is None:
        raise PermissionError(f"Path '{raw_target}' is outside workspace scope ({root}).")
    if not target.exists():
        raise FileNotFoundError(f"Path not found: {raw_target}")

    if target.is_file():
        if is_probably_binary(target) or target.stat().st_size > _MAX_INDEX_FILE_BYTES:
            return []
        return [(target.relative_to(root).as_posix(), target)]

    rel_prefix = target.relative_to(root).as_posix()
    all_rels = list_workspace_files(root)
    collected: list[tuple[str, Path]] = []
    for rel in all_rels:
        if rel_prefix != "." and not (rel == rel_prefix or rel.startswith(f"{rel_prefix}/")):
            continue
        full = root / rel
        if not full.is_file():
            continue
        try:
            if full.stat().st_size > _MAX_INDEX_FILE_BYTES:
                continue
        except OSError:
            continue
        if is_probably_binary(full):
            continue
        collected.append((rel, full))
    return collected

