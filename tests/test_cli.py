"""Tests for the CLI entry point and auth commands."""

from click.testing import CliRunner

from valkyrie import __version__
from valkyrie.cli.main import cli


def test_cli_shows_banner() -> None:
    """Running valkyrie with no args shows the banner."""
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "VALKYRIE" in result.output


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
