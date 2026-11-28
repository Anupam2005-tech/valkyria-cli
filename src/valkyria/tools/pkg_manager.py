"""
Package manager tool for Valkyria.

Provides a safe, approval-gated interface for installing, uninstalling, and
listing packages via pip, pipx, uv, npm/npx, cargo, brew, and apt/apt-get.

Design
------
- The user (or the agent) names a manager + action + package list.
- The tool resolves the exact shell command string and shows it *before* asking
  for approval.
- Execution is delegated to ``run_shell_command`` so the same denylist, timeout,
  and confirmation machinery applies.
- Each ``PackageManager`` entry maps to a canonical command template.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.tools import BaseTool, tool

from valkyria.core.cards import render_tool_card
from valkyria.tools.run_command import run_shell_command

if TYPE_CHECKING:
    from pathlib import Path

    from valkyria.tools.local_fs import ConfirmCallback

# ---------------------------------------------------------------------------
# Manager definitions
# ---------------------------------------------------------------------------

_MANAGERS: dict[str, dict[str, str]] = {
    # pip
    "pip": {
        "install": "pip install {packages}",
        "uninstall": "pip uninstall -y {packages}",
        "list": "pip list",
        "upgrade": "pip install --upgrade {packages}",
        "show": "pip show {packages}",
    },
    # pip3 (alias for systems where pip → pip2)
    "pip3": {
        "install": "pip3 install {packages}",
        "uninstall": "pip3 uninstall -y {packages}",
        "list": "pip3 list",
        "upgrade": "pip3 install --upgrade {packages}",
        "show": "pip3 show {packages}",
    },
    # uv — fast Python package manager
    "uv": {
        "install": "uv pip install {packages}",
        "uninstall": "uv pip uninstall {packages}",
        "list": "uv pip list",
        "upgrade": "uv pip install --upgrade {packages}",
        "sync": "uv pip sync {packages}",  # {packages} = requirements file
    },
    # pipx — application-level Python installs
    "pipx": {
        "install": "pipx install {packages}",
        "uninstall": "pipx uninstall {packages}",
        "list": "pipx list",
        "upgrade": "pipx upgrade {packages}",
        "upgrade-all": "pipx upgrade-all",
    },
    # npm
    "npm": {
        "install": "npm install {packages}",
        "uninstall": "npm uninstall {packages}",
        "list": "npm list --depth=0",
        "upgrade": "npm update {packages}",
        "ci": "npm ci",
        "run": "npm run {packages}",  # {packages} = script name
    },
    # yarn
    "yarn": {
        "install": "yarn add {packages}",
        "uninstall": "yarn remove {packages}",
        "list": "yarn list --depth=0",
        "upgrade": "yarn upgrade {packages}",
    },
    # pnpm
    "pnpm": {
        "install": "pnpm add {packages}",
        "uninstall": "pnpm remove {packages}",
        "list": "pnpm list",
        "upgrade": "pnpm update {packages}",
    },
    # cargo (Rust)
    "cargo": {
        "install": "cargo install {packages}",
        "uninstall": "cargo uninstall {packages}",
        "list": "cargo install --list",
        "update": "cargo update",
        "build": "cargo build",
        "test": "cargo test",
    },
    # brew (macOS / Linux Homebrew)
    "brew": {
        "install": "brew install {packages}",
        "uninstall": "brew uninstall {packages}",
        "list": "brew list",
        "upgrade": "brew upgrade {packages}",
        "update": "brew update",
    },
    # apt / apt-get (Debian/Ubuntu)
    "apt": {
        "install": "sudo apt-get install -y {packages}",
        "uninstall": "sudo apt-get remove -y {packages}",
        "list": "apt list --installed",
        "upgrade": "sudo apt-get upgrade -y {packages}",
        "update": "sudo apt-get update",
        "search": "apt-cache search {packages}",
    },
    "apt-get": {
        "install": "sudo apt-get install -y {packages}",
        "uninstall": "sudo apt-get remove -y {packages}",
        "list": "apt list --installed",
        "upgrade": "sudo apt-get upgrade -y {packages}",
        "update": "sudo apt-get update",
    },
    # dnf (Fedora/RHEL)
    "dnf": {
        "install": "sudo dnf install -y {packages}",
        "uninstall": "sudo dnf remove -y {packages}",
        "list": "dnf list installed",
        "upgrade": "sudo dnf upgrade -y {packages}",
        "update": "sudo dnf update -y",
    },
}

_KNOWN_MANAGERS = set(_MANAGERS)
_KNOWN_ACTIONS = {action for mgr in _MANAGERS.values() for action in mgr}


def _resolve_command(manager: str, action: str, packages: list[str]) -> str:
    """Build the exact shell command string for the given manager/action/packages."""
    mgr = manager.strip().lower()
    act = action.strip().lower()

    if mgr not in _MANAGERS:
        raise ValueError(
            f"Unknown package manager '{manager}'. Supported: {', '.join(sorted(_KNOWN_MANAGERS))}"
        )

    actions = _MANAGERS[mgr]
    if act not in actions:
        supported = ", ".join(sorted(actions.keys()))
        raise ValueError(f"Action '{action}' not supported for '{manager}'. Supported: {supported}")

    pkg_str = " ".join(packages) if packages else ""
    return actions[act].format(packages=pkg_str).strip()


# ---------------------------------------------------------------------------
# Core install function
# ---------------------------------------------------------------------------


def run_pkg_command(
    manager: str,
    action: str,
    packages: list[str],
    *,
    workspace_root: Path,
    confirm_fn: ConfirmCallback | None = None,
    auto_approve: bool = False,
    timeout_seconds: int = 300,
) -> str:
    """
    Resolve and execute a package manager command with approval gating.

    Args:
        manager: Package manager name (pip, npm, cargo, brew, apt, …).
        action: Action verb (install, uninstall, list, upgrade, …).
        packages: List of package names (empty for actions like 'list'/'update').
        workspace_root: Working directory for the subprocess.
        confirm_fn: Interactive approval callback (None → auto-approve).
        auto_approve: Skip confirmation when True.
        timeout_seconds: Kill threshold (default 300s for slow installs).

    Returns:
        Captured stdout/stderr string.
    """
    try:
        cmd = _resolve_command(manager, action, packages)
    except ValueError as exc:
        render_tool_card(
            tool="pkg",
            status="error",
            target=f"{manager} {action}",
            summary=str(exc),
        )
        return f"Error: {exc}"

    try:
        return run_shell_command(
            cmd,
            workspace_root=workspace_root,
            timeout_seconds=timeout_seconds,
            confirm_fn=confirm_fn,
            auto_approve=auto_approve,
        )
    except (PermissionError, RuntimeError, ValueError) as exc:
        return f"Error: {exc}"


# ---------------------------------------------------------------------------
# LangChain tool factory
# ---------------------------------------------------------------------------


def make_pkg_tool(
    workspace_root: Path,
    confirm_fn: ConfirmCallback | None = None,
    auto_approve: bool = False,
) -> BaseTool:
    """Return a LangChain ``BaseTool`` for package management."""

    @tool("pkg_install")
    def pkg_install_tool(
        manager: str,
        action: str,
        packages: list[str],
        timeout_seconds: int = 300,
    ) -> str:
        """
        Install, uninstall, list, or upgrade packages using pip, npm, cargo, brew, apt, etc.

        Use this when the user wants to download or install software, libraries,
        or CLI tools — e.g. "install requests", "npm install lodash", "brew install jq".

        Args:
            manager: Package manager to use. One of: pip, pip3, uv, pipx, npm, yarn,
                     pnpm, cargo, brew, apt, apt-get, dnf.
            action:  Action to perform. One of: install, uninstall, list, upgrade,
                     update, show, search, ci, run, build, test, sync.
            packages: List of package/library names. Pass [] for actions like 'list'
                      or 'update' that don't require a target.
            timeout_seconds: Kill threshold in seconds (default 300 for slow installs).
        """
        return run_pkg_command(
            manager,
            action,
            packages,
            workspace_root=workspace_root,
            confirm_fn=confirm_fn,
            auto_approve=auto_approve,
            timeout_seconds=timeout_seconds,
        )

    return pkg_install_tool
