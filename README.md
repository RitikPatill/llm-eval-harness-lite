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

## What Works (M1)

The following shipped in M1 and is functional after `pip install -e .`:

- **Package scaffold** — `src/evalite/` layout with `pyproject.toml` entry point; `evalite` command available on `$PATH` after install.
- **CLI stubs** — `evalite run` and `evalite diff` are registered and accept the expected arguments; both print a stub confirmation and exit cleanly.
- **Example suite** — `examples/qa_suite.yaml` demonstrates the YAML format.
- **Pinned dependencies** — `typer 0.12.3`, `rich 13.7.1`, `openai 1.35.3`, `pydantic 2.7.4`, `pyyaml 6.0.1` in both `requirements.txt` and `pyproject.toml`.
- **MIT license** and `.gitignore`.

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
    expected: "Gravity is a force that attracts objects with mass toward each other."
    scorer: contains
```

**Scorers:**

| Scorer | Description |
|--------|-------------|
| `exact` | Case-insensitive exact match |
| `contains` | Expected string found in output |
| `regex` | Output matches a regex pattern |
| `llm-judge` | Second LLM call scores output 0–1 against a rubric |

## Roadmap

| Milestone | Status | Description |
|-----------|--------|-------------|
| M1 | ✅ Done | Scaffold, README, CLI stub |
| M2 | Planned | YAML loader + scorer engine (exact, contains, regex) |
| M3 | Planned | LLM runner + llm-judge scorer |
| M4 | Planned | Rich terminal UI + JSON result snapshots |
| M5 | Planned | `evalite diff` result comparison |

## License

MIT — see [LICENSE](LICENSE).
