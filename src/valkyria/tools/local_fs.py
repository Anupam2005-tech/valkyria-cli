"""
Local machine filesystem CRUD tools wrapped as LangChain BaseTool instances.

Supports creating, reading, editing/updating, deleting, listing, and searching
files across the workspace and allowed user directories (e.g. ~/Downloads).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from langchain_core.tools import BaseTool, tool

from valkyria.core.cards import render_tool_card
from valkyria.core.workspace import _IGNORED_DIRS

ConfirmCallback = Callable[[str, str, str | None], bool]

_BLOCKED_SYSTEM_ROOTS = (
    Path("/etc"),
    Path("/bin"),
    Path("/sbin"),
    Path("/usr"),
    Path("/boot"),
    Path("/sys"),
    Path("/proc"),
    Path("/dev"),
    Path("/lib"),
    Path("/lib64"),
)

_PROTECTED_FILENAMES = {"vault.enc", "auth.json", ".env"}
_MAX_READ_CHARS = 16_000


def _display_path(target: Path, workspace_root: Path) -> str:
    """Format path relative to workspace when inside it, otherwise with ~ when under HOME."""
    try:
        return str(target.relative_to(workspace_root.resolve()))
    except ValueError:
        home = Path.home().resolve()
        try:
            return f"~/{target.relative_to(home)}"
        except ValueError:
            return str(target)


def resolve_local_path(raw_path: str, workspace_root: Path) -> Path:
    """
    Resolve a local path safely across workspace or home/absolute paths.

    Blocks system OS directories and Valkyria credential/secret files.
    """
    cleaned = raw_path.strip()
    if not cleaned:
        raise ValueError("Path cannot be empty.")

    expanded = os.path.expandvars(os.path.expanduser(cleaned))
    candidate = Path(expanded)
    if not candidate.is_absolute():
        candidate = workspace_root.resolve() / candidate
    resolved = candidate.resolve(strict=False)

    # Helpful fallback if user references ~/download/... instead of ~/Downloads/...
    if not resolved.exists() and not resolved.parent.exists():
        home = Path.home().resolve()
        downloads = home / "Downloads"
        try:
            rel_home = resolved.relative_to(home)
            if (
                rel_home.parts
                and rel_home.parts[0].lower() in ("download", "downloads")
                and downloads.exists()
            ):
                resolved = (downloads.joinpath(*rel_home.parts[1:])).resolve(strict=False)
        except ValueError:
            pass

    for root in _BLOCKED_SYSTEM_ROOTS:
        if resolved == root or root in resolved.parents:
            raise PermissionError(f"Blocked access to protected system path: {resolved}")

    if resolved.name in _PROTECTED_FILENAMES:
        raise PermissionError(
            f"Blocked access to protected credential/secret file: {resolved.name}"
        )

    if ".git" in resolved.parts:
        raise PermissionError("Blocked access inside .git metadata directory.")

    return resolved


def local_read_file(
    workspace_root: Path,
    path: str,
    *,
    start_line: int = 1,
    end_line: int = 250,
) -> str:
    """Read a UTF-8 text file from the local machine."""
    target = resolve_local_path(path, workspace_root)
    if not target.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if target.is_dir():
        raise ValueError(f"Path is a directory, not a file: {path}")

    raw_bytes = target.read_bytes()
    if b"\x00" in raw_bytes[:4096]:
        raise ValueError(f"Cannot read binary file: {path}")

    lines = raw_bytes.decode("utf-8", errors="replace").splitlines()
    total = len(lines)
    start = max(1, start_line)
    end = min(total, max(start, end_line)) if total > 0 else 0
    slice_lines = lines[start - 1 : end] if total > 0 else []
    numbered = "\n".join(
        f"{idx}: {line}" for idx, line in enumerate(slice_lines, start=start)
    )
    if len(numbered) > _MAX_READ_CHARS:
        numbered = numbered[:_MAX_READ_CHARS] + "\n... [truncated]"

    disp = _display_path(target, workspace_root)
    render_tool_card(
        tool="read",
        status="ok",
        target=disp,
        summary=f"L{start}-L{end} of {total} lines",
    )
    return f"File: {disp} (lines {start}-{end} of {total})\n{numbered}"


def local_write_file(
    workspace_root: Path,
    path: str,
    content: str,
    *,
    overwrite: bool = True,
    confirm_fn: ConfirmCallback | None = None,
) -> str:
    """Create or overwrite a file on the local machine."""
    target = resolve_local_path(path, workspace_root)
    existed = target.exists()
    if existed and target.is_dir():
        raise ValueError(f"Target is an existing directory: {path}")
    if existed and not overwrite:
        raise FileExistsError(f"File already exists and overwrite=False: {path}")

    disp = _display_path(target, workspace_root)
    line_count = len(content.splitlines()) or (1 if content else 0)
    action_label = "overwrite" if existed else "create"
    preview_lines = content.splitlines()[:10]
    preview = "\n".join(preview_lines)
    if len(content.splitlines()) > 10:
        preview += "\n..."

    if confirm_fn is not None and not confirm_fn(f"{action_label}_file", disp, preview):
        render_tool_card(
            tool="write",
            status="blocked",
            target=disp,
            summary="Cancelled by user.",
        )
        return f"User declined to {action_label} file '{disp}'."

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    byte_count = target.stat().st_size

    verb = "Updated" if existed else "Created"
    render_tool_card(
        tool="write",
        status="ok",
        target=disp,
        summary=f"{verb} {line_count} line(s), {byte_count:,} bytes",
        details=preview or "(empty file)",
    )
    return f"{verb} {target} ({line_count} lines, {byte_count} bytes)."


def local_edit_file(
    workspace_root: Path,
    path: str,
    target_text: str,
    replacement: str,
    *,
    replace_all: bool = False,
    confirm_fn: ConfirmCallback | None = None,
) -> str:
    """Update an existing file by replacing an exact target snippet."""
    target = resolve_local_path(path, workspace_root)
    if not target.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if target.is_dir():
        raise ValueError(f"Target is a directory: {path}")

    original = target.read_text(encoding="utf-8", errors="replace")
    if target_text not in original:
        raise ValueError(
            "Target snippet not found in file. Call read_file first to verify exact text."
        )

    occurrences = original.count(target_text)
    if occurrences > 1 and not replace_all:
        raise ValueError(
            f"Target snippet matched {occurrences} times. Provide more surrounding context "
            "or pass replace_all=True."
        )

    updated = (
        original.replace(target_text, replacement)
        if replace_all
        else original.replace(target_text, replacement, 1)
    )
    disp = _display_path(target, workspace_root)
    diff_preview = "\n".join(
        [f"- {line}" for line in target_text.splitlines()[:5]]
        + [f"+ {line}" for line in replacement.splitlines()[:5]]
    )

    if confirm_fn is not None and not confirm_fn("edit_file", disp, diff_preview):
        render_tool_card(
            tool="edit",
            status="blocked",
            target=disp,
            summary="Edit cancelled by user.",
        )
        return f"User declined to edit '{disp}'."

    target.write_text(updated, encoding="utf-8")
    applied = occurrences if replace_all else 1
    render_tool_card(
        tool="edit",
        status="ok",
        target=disp,
        summary=f"Applied {applied} replacement(s)",
        details=diff_preview,
    )
    return f"Updated {target} ({applied} replacement(s))."


def local_delete_file(
    workspace_root: Path,
    path: str,
    *,
    confirm_fn: ConfirmCallback | None = None,
) -> str:
    """Delete a file on the local machine (does not recursively delete directories)."""
    target = resolve_local_path(path, workspace_root)
    if not target.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if target.is_dir():
        raise ValueError(f"Refusing to delete directory '{path}'; only files may be deleted.")

    disp = _display_path(target, workspace_root)
    size = target.stat().st_size

    if confirm_fn is not None and not confirm_fn(
        "delete_file", disp, f"Delete file permanently ({size:,} bytes)?"
    ):
        render_tool_card(
            tool="delete",
            status="blocked",
            target=disp,
            summary="Deletion cancelled by user.",
        )
        return f"User declined to delete '{disp}'."

    target.unlink()
    render_tool_card(
        tool="delete",
        status="ok",
        target=disp,
        summary=f"Deleted file ({size:,} bytes)",
    )
    return f"Deleted {target}."


def local_list_directory(
    workspace_root: Path,
    path: str = ".",
    *,
    pattern: str = "*",
    max_entries: int = 80,
) -> str:
    """List files and subdirectories in a local folder."""
    target = resolve_local_path(path, workspace_root)
    if not target.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not target.is_dir():
        raise ValueError(f"Not a directory: {path}")

    entries: list[str] = []
    for item in sorted(target.glob(pattern), key=lambda p: (not p.is_dir(), p.name.lower())):
        if item.name in _IGNORED_DIRS:
            continue
        if item.is_dir():
            entries.append(f"{item.name}/")
        else:
            entries.append(f"{item.name} ({item.stat().st_size:,} B)")
        if len(entries) >= max_entries:
            break

    disp = _display_path(target, workspace_root)
    render_tool_card(
        tool="listdir",
        status="ok",
        target=disp,
        summary=f"{len(entries)} item(s) matching '{pattern}'",
    )
    return f"Directory {disp}:\n" + ("\n".join(entries) if entries else "(empty)")


def local_search_files(
    workspace_root: Path,
    query: str,
    *,
    path: str = ".",
    max_matches: int = 30,
) -> str:
    """Search file contents case-insensitively inside a local folder."""
    target = resolve_local_path(path, workspace_root)
    if not target.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    needle = query.lower()
    matches: list[str] = []
    candidates = [target] if target.is_file() else sorted(target.rglob("*"))
    for p in candidates:
        if any(part in _IGNORED_DIRS for part in p.parts):
            continue
        if not p.is_file() or p.stat().st_size > 512_000:
            continue
        raw = p.read_bytes()
        if b"\x00" in raw[:2048]:
            continue
        for lineno, line in enumerate(
            raw.decode("utf-8", errors="replace").splitlines(), start=1
        ):
            if needle in line.lower():
                rel = _display_path(p, workspace_root)
                matches.append(f"{rel}:{lineno}: {line.strip()[:140]}")
                if len(matches) >= max_matches:
                    break
        if len(matches) >= max_matches:
            break

    disp = _display_path(target, workspace_root)
    render_tool_card(
        tool="grep",
        status="ok",
        target=f"{query} in {disp}",
        summary=f"{len(matches)} match(es)",
    )
    return "\n".join(matches) if matches else f"No matches found for '{query}' in {disp}."


def make_local_tools(
    workspace_root: Path,
    confirm_fn: ConfirmCallback | None = None,
) -> list[BaseTool]:
    """Create LangChain BaseTool instances bound to the workspace and confirmation callback."""

    @tool("read_file")
    def read_file_tool(path: str, start_line: int = 1, end_line: int = 250) -> str:
        """Read lines from a file on the local machine (workspace, ~/Downloads, or full path)."""
        return local_read_file(workspace_root, path, start_line=start_line, end_line=end_line)

    @tool("write_file")
    def write_file_tool(path: str, content: str, overwrite: bool = True) -> str:
        """Create a new file or overwrite an existing file on the local machine."""
        return local_write_file(
            workspace_root,
            path,
            content,
            overwrite=overwrite,
            confirm_fn=confirm_fn,
        )

    @tool("edit_file")
    def edit_file_tool(
        path: str,
        target: str,
        replacement: str,
        replace_all: bool = False,
    ) -> str:
        """Update an existing local file by replacing an exact snippet with replacement text."""
        return local_edit_file(
            workspace_root,
            path,
            target,
            replacement,
            replace_all=replace_all,
            confirm_fn=confirm_fn,
        )

    @tool("delete_file")
    def delete_file_tool(path: str) -> str:
        """Delete a file from the local machine."""
        return local_delete_file(workspace_root, path, confirm_fn=confirm_fn)

    @tool("list_directory")
    def list_directory_tool(path: str = ".", pattern: str = "*", max_entries: int = 80) -> str:
        """List files and subdirectories in a local directory (workspace or ~/Downloads, etc.)."""
        return local_list_directory(
            workspace_root, path, pattern=pattern, max_entries=max_entries
        )

    @tool("search_files")
    def search_files_tool(query: str, path: str = ".", max_matches: int = 30) -> str:
        """Search text inside files within a local directory."""
        return local_search_files(workspace_root, query, path=path, max_matches=max_matches)

    return [
        read_file_tool,
        write_file_tool,
        edit_file_tool,
        delete_file_tool,
        list_directory_tool,
        search_files_tool,
    ]
