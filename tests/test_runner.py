from unittest.mock import MagicMock

import pytest

from evalite.runner import (
    CaseResult,
    score_contains,
    score_exact,
    score_llm_judge,
    score_regex,
    run_suite,
)
from evalite.schema import EvalCase, EvalSuite


def _make_response(content: str, prompt_tokens: int = 10, completion_tokens: int = 5):
    """Build a minimal mock mimicking openai.types.chat.ChatCompletion."""
    response = MagicMock()
    response.choices[0].message.content = content
    response.usage.prompt_tokens = prompt_tokens
    response.usage.completion_tokens = completion_tokens
    return response


# --- pure scorer tests ---

def test_score_exact_pass():
    assert score_exact("Paris", "Paris") == 1.0


def test_score_exact_fail():
    assert score_exact("Lyon", "Paris") == 0.0


def test_score_contains_pass():
    assert score_contains("Gravity is a force.", "force") == 1.0


def test_score_contains_fail():
    assert score_contains("Nothing here.", "force") == 0.0


def test_score_regex_pass():
    assert score_regex("Python 3.6 added f-strings", r"^3\.6") == 0.0
    assert score_regex("3.6", r"^3\.6") == 1.0


def test_score_llm_judge_parses_float():
    client = MagicMock()
    client.chat.completions.create.return_value = _make_response("0.8")
    result = score_llm_judge("some answer", "expected", None, client, "gpt-4o-mini")
    assert result == 0.8


def test_score_llm_judge_clamps():
    client = MagicMock()
    client.chat.completions.create.return_value = _make_response("1.5")
    result = score_llm_judge("some answer", "expected", None, client, "gpt-4o-mini")
    assert result == 1.0


def test_score_llm_judge_raises_on_non_numeric():
    client = MagicMock()
    client.chat.completions.create.return_value = _make_response("good job!")
    with pytest.raises(ValueError, match="non-numeric"):
        score_llm_judge("some answer", "expected", None, client, "gpt-4o-mini")


# --- run_suite tests ---

def _one_case_suite(scorer: str, expected: str = "Paris", rubric: str | None = None) -> EvalSuite:
    return EvalSuite(
        suite="test",
        cases=[
            EvalCase(
                id="case1",
                prompt="What is the capital of France?",
                expected=expected,
                scorer=scorer,
                rubric=rubric,
            )
        ],
    )


def test_run_suite_exact():
    client = MagicMock()
    client.chat.completions.create.return_value = _make_response("Paris")
    suite = _one_case_suite("exact", expected="Paris")
    results = run_suite(suite, "gpt-4o-mini", client)
    assert len(results) == 1
    assert results[0].passed is True
    assert results[0].score == 1.0


def test_run_suite_records_latency():
    client = MagicMock()
    client.chat.completions.create.return_value = _make_response("Paris")
    suite = _one_case_suite("exact", expected="Paris")
    results = run_suite(suite, "gpt-4o-mini", client)
    assert results[0].latency_ms >= 0


def test_run_suite_llm_judge():
    client = MagicMock()
    # First call for the actual LLM response, second for the judge
    client.chat.completions.create.side_effect = [
        _make_response("Paris is the capital city of France."),
        _make_response("0.9"),
    ]
    suite = _one_case_suite(
        "llm-judge",
        expected="Should mention Paris",
        rubric="The answer should mention Paris as the capital of France.",
    )
    results = run_suite(suite, "gpt-4o-mini", client)
    assert results[0].passed is True
    assert results[0].score == 0.9


def test_run_suite_token_counts():
    client = MagicMock()
    client.chat.completions.create.return_value = _make_response(
        "Paris", prompt_tokens=12, completion_tokens=3
    )
    suite = _one_case_suite("exact", expected="Paris")
    results = run_suite(suite, "gpt-4o-mini", client)
    assert results[0].prompt_tokens == 12
    assert results[0].completion_tokens == 3
