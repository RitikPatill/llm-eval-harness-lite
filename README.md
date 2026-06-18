# llm-eval-harness-lite

**The `pytest` of LLM outputs** — define eval suites in YAML, run them locally, catch regressions before shipping.

## Motivation

Evaluating LLM outputs is the #1 pain point for teams shipping AI features. Existing solutions (LangSmith, RAGAS, OpenAI Evals) are either cloud-only, overly complex, or tightly coupled to a specific framework. This tool is:

- **Framework-agnostic** — works with any OpenAI-compatible API
- **Offline-first** — no cloud account required (except the LLM call itself)
- **Git-friendly** — results stored as plain JSON, easy to diff

## Installation

```bash
pip install -e .
```

Requires Python 3.10+.

## What Works (M2)

The following shipped in M2 and is functional after `pip install -e .`:

- **Package scaffold** — `src/evalite/` layout with `pyproject.toml` entry point; `evalite` command available on `$PATH` after install.
- **CLI stubs** — `evalite run` and `evalite diff` are registered and accept the expected arguments; both print a stub confirmation and exit cleanly.
- **Pydantic schema** — `EvalCase` and `EvalSuite` models in `src/evalite/schema.py` validate suite YAML with clear enum errors for unknown scorers.
- **YAML loader** — `load_suite(path)` in `src/evalite/loader.py` reads and validates a YAML file, raising `ValueError` with a human-readable message on any schema violation.
- **Example suite** — `examples/qa_suite.yaml` has 5 cases covering `exact`, `contains`, and `regex` scorers.
- **Tests** — `pytest tests/test_loader.py` verifies the happy path and two error paths (invalid scorer, missing field).
- **Pinned dependencies** — `typer 0.12.3`, `rich 13.7.1`, `openai 1.35.3`, `pydantic 2.7.4`, `pyyaml 6.0.1`, `pytest 8.2.2` in `requirements.txt`.
- **MIT license** and `.gitignore`.

### Run tests

```bash
pip install -e .
pytest tests/test_loader.py -v
```

## Planned Usage

> The CLI is installed and commands accept arguments, but execution logic is not yet implemented (see Roadmap). Commands currently print a stub confirmation and exit.

**Run an eval suite:**

```bash
evalite run examples/qa_suite.yaml --model gpt-4o-mini
```

**Diff two result snapshots:**

```bash
evalite diff results/2024-01-01_120000.json results/2024-01-02_120000.json
```

## Architecture

```
src/evalite/
├── __init__.py
├── cli.py        # Typer app; `run` and `diff` command stubs
├── schema.py     # Pydantic models: EvalCase, EvalSuite
└── loader.py     # load_suite(path) — reads YAML, validates schema, returns EvalSuite
```

The CLI layer is intentionally thin. Execution logic (LLM calls, scoring, output) will be added in M3–M4 as separate modules.

## YAML Eval Suite Format

```yaml
suite: qa_basics
cases:
  - id: capital_france
    prompt: "What is the capital of France?"
    expected: "Paris"
    scorer: exact

  - id: explain_gravity
    prompt: "Explain gravity in one sentence."
    expected: "force"
    scorer: contains

  - id: py_version_check
    prompt: "What Python version introduced f-strings?"
    expected: "^3\\.6"
    scorer: regex

  - id: code_quality
    prompt: "Write a Python function that adds two numbers."
    expected: "correct and idiomatic"
    scorer: llm-judge
    rubric: "The function should use a def statement, accept two parameters, and return their sum."
```

All fields except `rubric` are required. `rubric` is only used by the `llm-judge` scorer.

**Scorers:**

| Scorer | Description |
|--------|-------------|
| `exact` | Case-insensitive exact match |
| `contains` | Expected string found anywhere in output |
| `regex` | Output matches a regex pattern |
| `llm-judge` | Second LLM call scores output 0–1 against a rubric (requires M3 runner) |

## Roadmap

| Milestone | Status | Description |
|-----------|--------|-------------|
| M1 | ✅ Done | Scaffold, README, CLI stub |
| M2 | ✅ Done | Pydantic schema, YAML loader, 5-case example suite, tests |
| M3 | Planned | LLM runner + llm-judge scorer |
| M4 | Planned | Rich terminal UI + JSON result snapshots |
| M5 | Planned | `evalite diff` result comparison |

## License

MIT — see [LICENSE](LICENSE).
