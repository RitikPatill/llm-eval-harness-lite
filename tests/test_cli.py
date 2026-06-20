from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from evalite.cli import app
from evalite.runner import CaseResult

runner = CliRunner()

_MOCK_RESULTS = [
    CaseResult(
        id="capital_france",
        prompt="What is the capital of France?",
        expected="Paris",
        scorer="exact",
        actual="Paris",
        score=1.0,
        passed=True,
        latency_ms=312.4,
        prompt_tokens=14,
        completion_tokens=3,
    ),
    CaseResult(
        id="explain_gravity",
        prompt="Explain gravity in one sentence.",
        expected="force",
        scorer="contains",
        actual="Gravity is a fundamental force.",
        score=1.0,
        passed=True,
        latency_ms=420.0,
        prompt_tokens=12,
        completion_tokens=8,
    ),
]


def test_run_writes_snapshot(tmp_path: Path) -> None:
    suite_path = Path("examples/qa_suite.yaml")
    with (
        patch("evalite.cli.run_suite", return_value=_MOCK_RESULTS),
        patch("evalite.cli.openai.OpenAI", return_value=MagicMock()),
    ):
        result = runner.invoke(
            app,
            ["run", str(suite_path), "--output-dir", str(tmp_path)],
        )

    assert result.exit_code == 0, result.output

    json_files = list(tmp_path.glob("*.json"))
    assert len(json_files) == 1

    data = json.loads(json_files[0].read_text())
    assert len(data) == 2
    assert data[0]["id"] == "capital_france"
    assert data[0]["score"] == 1.0
    assert data[0]["passed"] is True
    assert data[1]["id"] == "explain_gravity"


def test_run_missing_suite_exits_nonzero() -> None:
    result = runner.invoke(app, ["run", "nonexistent.yaml"])
    assert result.exit_code != 0


def test_diff_shows_regression(tmp_path: Path) -> None:
    run_a = tmp_path / "run_a.json"
    run_b = tmp_path / "run_b.json"

    run_a.write_text(
        json.dumps([
            {"id": "q1", "score": 1.0, "passed": True, "scorer": "exact"},
        ])
    )
    run_b.write_text(
        json.dumps([
            {"id": "q1", "score": 0.0, "passed": False, "scorer": "exact"},
        ])
    )

    result = runner.invoke(app, ["diff", str(run_a), str(run_b)])
    assert result.exit_code == 0, result.output
    assert "REGRESSED" in result.output


def test_diff_shows_improvement(tmp_path: Path) -> None:
    run_a = tmp_path / "run_a.json"
    run_b = tmp_path / "run_b.json"

    run_a.write_text(
        json.dumps([
            {"id": "q1", "score": 0.0, "passed": False, "scorer": "exact"},
        ])
    )
    run_b.write_text(
        json.dumps([
            {"id": "q1", "score": 1.0, "passed": True, "scorer": "exact"},
        ])
    )

    result = runner.invoke(app, ["diff", str(run_a), str(run_b)])
    assert result.exit_code == 0, result.output
    assert "IMPROVED" in result.output
