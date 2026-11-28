"""Tests for the CLI entry point and auth commands."""

from __future__ import annotations

import importlib.metadata
import subprocess
import sys

from click.testing import CliRunner

from valkyria import __app_name__, __version__
from valkyria.cli.main import cli


def test_cli_shows_banner() -> None:
    """Running valkyria with no args shows the banner."""
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "VALKYRIA" in result.output


def test_cli_version() -> None:
    """--version prints the version string."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_status_command() -> None:
    """status command runs and shows config directory."""
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Status" in result.output


def test_auth_status() -> None:
    """auth status shows authentication state."""
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "status"])
    assert result.exit_code == 0
    assert "Authentication" in result.output


def test_auth_logout_when_not_signed_in() -> None:
    """auth logout when not signed in shows info message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "logout"])
    assert result.exit_code == 0
    assert "Not signed in" in result.output


def test_auth_help() -> None:
    """auth --help shows the auth command group."""
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "--help"])
    assert result.exit_code == 0
    assert "login" in result.output
    assert "switch" in result.output
    assert "delete" in result.output
    assert "logout" in result.output
    assert "status" in result.output


def test_short_cli_aliases() -> None:
    """Short CLI aliases (s, m, a) resolve to their full commands."""
    runner = CliRunner()
    res_status = runner.invoke(cli, ["s"])
    assert res_status.exit_code == 0
    assert "Status" in res_status.output

    res_auth = runner.invoke(cli, ["a", "--help"])
    assert res_auth.exit_code == 0
    assert "switch" in res_auth.output


def test_package_metadata_and_module_entrypoint() -> None:
    """Package metadata, console scripts, and `python -m valkyria` reflect the valkyria rename."""
    assert __app_name__ == "valkyria"

    proc = subprocess.run(
        [sys.executable, "-m", "valkyria", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert f"valkyria, version {__version__}" in proc.stdout

    try:
        dist = importlib.metadata.distribution("valkyria-cli")
    except importlib.metadata.PackageNotFoundError:
        return

    assert dist.version == __version__
    scripts = {ep.name: ep.value for ep in dist.entry_points if ep.group == "console_scripts"}
    assert scripts == {
        "valkyria": "valkyria.cli.main:cli",
        "vk": "valkyria.cli.main:cli",
    }
