"""Phase 0 smoke test：验证包可导入、CLI 骨架可运行。"""

from __future__ import annotations

from typer.testing import CliRunner

import starrupture_agent_skills
from starrupture_agent_skills.cli.main import app

runner = CliRunner()


def test_package_importable() -> None:
    assert starrupture_agent_skills.__version__


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "starrupture" in result.output


def test_cli_plan_help() -> None:
    result = runner.invoke(app, ["plan", "--help"])
    assert result.exit_code == 0
    assert "--rate" in result.output


def test_cli_plan_runs() -> None:
    result = runner.invoke(app, ["plan", "Battery", "--rate", "60"])
    assert result.exit_code == 0
    assert "Battery" in result.output


def test_cli_recipe_runs() -> None:
    result = runner.invoke(app, ["recipe", "Battery"])
    assert result.exit_code == 0
    assert "Battery" in result.output
