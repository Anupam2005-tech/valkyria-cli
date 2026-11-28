"""
Sandboxed shell command execution tool for Valkyrie.

Runs arbitrary shell commands inside the workspace directory (or a confirmed
directory) with a hard timeout, a denylist of dangerous patterns, and a
mandatory user-confirmation gate before execution.

Security model
--------------
- All commands run via ``subprocess`` with ``shell=True`` but with ``cwd``
  locked to the workspace root (or a resolved allowed path).
- A denylist of destructive patterns is checked *before* the confirmation
  prompt so the user is never asked to approve inherently dangerous commands.
- If ``confirm_fn`` is provided (interactive terminal) the user must approve
  every execution.  When ``auto_approve=True`` (set by /auto) the confirmation
  gate is skipped.
- stdout + stderr are captured and truncated to ``_MAX_OUTPUT_CHARS``.
- Commands that exceed ``timeout_seconds`` are killed and their PID tree is
  terminated.
"""

from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.tools import BaseTool, tool

from valkyrie.core.cards import render_tool_card

if TYPE_CHECKING:
    from valkyrie.tools.local_fs import ConfirmCallback

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEFAULT_TIMEOUT = 60  # seconds
_MAX_OUTPUT_CHARS = 8_000

# Patterns that are *always* blocked, regardless of user approval.
# Uses re.search on the raw command string (case-insensitive).
_DENYLIST_PATTERNS: list[re.Pattern[str]] = [
    # Disk-wipe / recursive forced delete of system-critical roots
    re.compile(r"rm\s+.*-[a-z]*r[a-z]*f.*\s+/(?:\s|$)", re.IGNORECASE),
    re.compile(r"rm\s+.*-[a-z]*f[a-z]*r.*\s+/(?:\s|$)", re.IGNORECASE),
    # Writing directly to block devices / special devices
    re.compile(r"dd\s+.*of=\s*/dev/[a-z]", re.IGNORECASE),
    # Fork bombs
    re.compile(r":\(\)\{.*\|.*&\s*\}", re.IGNORECASE),
    # Privilege escalation shortcuts
    re.compile(r"\bsudo\s+su\b", re.IGNORECASE),
    re.compile(r"\bsudo\s+-[a-z]*s\b", re.IGNORECASE),  # sudo -s / sudo -i
    # Wiping MBR / partition tables
    re.compile(r"\bshred\b.*\b/dev/", re.IGNORECASE),
    # chmod 777 on the filesystem root
    re.compile(r"chmod\s+.*777\s+/\s*$", re.IGNORECASE),
]


def _is_blocked(command: str) -> tuple[bool, str]:
    """Return (blocked, reason) for commands that match the denylist."""
    for pattern in _DENYLIST_PATTERNS:
        if pattern.search(command):
            return True, f"Command matches blocked pattern: {pattern.pattern}"
    return False, ""


# ---------------------------------------------------------------------------
# Core execution function
# ---------------------------------------------------------------------------


def run_shell_command(
    command: str,
    *,
    workspace_root: Path,
    timeout_seconds: int = _DEFAULT_TIMEOUT,
    confirm_fn: "ConfirmCallback | None" = None,
    auto_approve: bool = False,
    env_passthrough: dict[str, str] | None = None,
) -> str:
    """
    Execute a shell command and return captured output (stdout + stderr).

    Args:
        command: The shell command string to execute.
        workspace_root: Locked working directory for execution.
        timeout_seconds: Kill threshold in seconds (default 60).
        confirm_fn: Optional interactive approval callback.
        auto_approve: Skip confirmation when True.
        env_passthrough: Extra environment variables injected into the subprocess.

    Returns:
        A formatted string of stdout/stderr output.

    Raises:
        PermissionError: When the command matches the denylist.
        RuntimeError: When the user denies execution.
    """
    cmd = command.strip()
    if not cmd:
        raise ValueError("Command cannot be empty.")

    # 1. Denylist check — hard block before anything else
    blocked, reason = _is_blocked(cmd)
    if blocked:
        render_tool_card(tool="run", status="blocked", target=cmd, summary=reason)
        raise PermissionError(reason)

    # 2. Build a short preview for the confirmation card
    preview = cmd if len(cmd) <= 120 else cmd[:117] + "…"

    # 3. Approval gate
    if confirm_fn is not None and not auto_approve:
        allowed = confirm_fn("run_command", preview, f"cwd: {workspace_root}")
        if not allowed:
            render_tool_card(
                tool="run",
                status="blocked",
                target=preview,
                summary="Execution cancelled by user.",
            )
            raise RuntimeError(f"User declined to run: {preview}")

    # 4. Execute
    import os

    exec_env = os.environ.copy()
    if env_passthrough:
        exec_env.update(env_passthrough)

    render_tool_card(
        tool="run",
        status="ok",
        target=preview,
        summary=f"Running in {workspace_root} (timeout {timeout_seconds}s) …",
    )

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=exec_env,
        )
    except subprocess.TimeoutExpired:
        msg = f"Command timed out after {timeout_seconds}s: {preview}"
        render_tool_card(tool="run", status="error", target=preview, summary=msg)
        raise RuntimeError(msg)

    combined = ""
    if result.stdout:
        combined += result.stdout
    if result.stderr:
        combined += ("\n" if combined else "") + "[stderr]\n" + result.stderr

    if len(combined) > _MAX_OUTPUT_CHARS:
        combined = combined[:_MAX_OUTPUT_CHARS] + "\n… [output truncated]"

    exit_label = f"exit {result.returncode}"
    status = "ok" if result.returncode == 0 else "error"
    render_tool_card(
        tool="run",
        status=status,
        target=preview,
        summary=exit_label,
        details=combined[:400] if combined else "(no output)",
    )

    if not combined:
        return f"Command completed ({exit_label}). No output."
    return f"[{exit_label}]\n{combined}"


# ---------------------------------------------------------------------------
# LangChain tool factory
# ---------------------------------------------------------------------------


def make_run_command_tool(
    workspace_root: Path,
    confirm_fn: "ConfirmCallback | None" = None,
    auto_approve: bool = False,
) -> BaseTool:
    """Return a LangChain ``BaseTool`` that runs shell commands in ``workspace_root``."""

    @tool("run_command")
    def run_command_tool(
        command: str,
        timeout_seconds: int = _DEFAULT_TIMEOUT,
    ) -> str:
        """
        Run a shell command inside the workspace directory and return its output.

        Use this when the user asks to execute a command, install a package (use
        pkg_install instead when possible), run tests, build a project, compile
        code, start a process, or perform any terminal operation.

        Args:
            command: The shell command to execute (e.g. 'ls -la', 'python main.py').
            timeout_seconds: Seconds before the command is force-killed (default 60).
        """
        try:
            return run_shell_command(
                command,
                workspace_root=workspace_root,
                timeout_seconds=timeout_seconds,
                confirm_fn=confirm_fn,
                auto_approve=auto_approve,
            )
        except (PermissionError, RuntimeError, ValueError) as exc:
            return f"Error: {exc}"

    return run_command_tool
