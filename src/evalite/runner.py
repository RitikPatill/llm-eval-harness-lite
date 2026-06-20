from __future__ import annotations

import re
import time
from dataclasses import dataclass

import openai

from evalite.schema import EvalSuite

PASS_THRESHOLD_DETERMINISTIC = 1.0
PASS_THRESHOLD_JUDGE = 0.5

_JUDGE_SYSTEM = (
    "You are an impartial grader. Given a rubric and a response, output ONLY a number\n"
    "between 0.0 and 1.0 representing quality. Output nothing else.\n\n"
    "Rubric: {rubric}\n"
    "Response: {response}"
)


@dataclass
class CaseResult:
    id: str
    prompt: str
    expected: str
    scorer: str
    actual: str
    score: float
    passed: bool
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int


def score_exact(actual: str, expected: str) -> float:
    return 1.0 if actual.strip() == expected.strip() else 0.0


def score_contains(actual: str, expected: str) -> float:
    return 1.0 if expected.strip().lower() in actual.lower() else 0.0


def score_regex(actual: str, pattern: str) -> float:
    return 1.0 if re.search(pattern, actual) else 0.0


def score_llm_judge(
    actual: str,
    expected: str,
    rubric: str | None,
    client: openai.OpenAI,
    model: str,
) -> float:
    prompt = _JUDGE_SYSTEM.format(rubric=rubric or expected, response=actual)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.choices[0].message.content or ""
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        raise ValueError(f"llm-judge returned non-numeric response: {text!r}")
    return min(1.0, max(0.0, float(match.group(1))))


def run_suite(
    suite: EvalSuite,
    model: str,
    client: openai.OpenAI,
) -> list[CaseResult]:
    results: list[CaseResult] = []
    for case in suite.cases:
        t0 = time.monotonic()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": case.prompt}],
        )
        latency_ms = (time.monotonic() - t0) * 1000

        actual = response.choices[0].message.content or ""
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        scorer = case.scorer
        if scorer == "exact":
            score = score_exact(actual, case.expected)
            passed = score >= PASS_THRESHOLD_DETERMINISTIC
        elif scorer == "contains":
            score = score_contains(actual, case.expected)
            passed = score >= PASS_THRESHOLD_DETERMINISTIC
        elif scorer == "regex":
            score = score_regex(actual, case.expected)
            passed = score >= PASS_THRESHOLD_DETERMINISTIC
        elif scorer == "llm-judge":
            score = score_llm_judge(actual, case.expected, case.rubric, client, model)
            passed = score >= PASS_THRESHOLD_JUDGE
        else:
            raise ValueError(f"Unknown scorer: {scorer!r}")

        results.append(
            CaseResult(
                id=case.id,
                prompt=case.prompt,
                expected=case.expected,
                scorer=scorer,
                actual=actual,
                score=score,
                passed=passed,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        )
    return results
