from __future__ import annotations

import dataclasses
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

import openai
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from evalite.loader import load_suite
from evalite.runner import CaseResult, run_suite

app = typer.Typer(help="LLM Eval Harness Lite — the pytest of LLM outputs.")
console = Console()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _print_table(results: list[CaseResult], suite_name: str, model: str) -> None:
    table = Table(title=f"Suite: {suite_name}  |  Model: {model}", show_lines=False)
    table.add_column("ID", style="bold")
    table.add_column("Scorer")
    table.add_column("Score", justify="right")
    table.add_column("Pass", justify="center")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Tokens (p+c)", justify="right")

    for r in results:
        color = "green" if r.passed else "red"
        table.add_row(
            r.id,
            r.scorer,
            f"[{color}]{r.score:.2f}[/{color}]",
            f"[{color}]{'✓' if r.passed else '✗'}[/{color}]",
            str(int(r.latency_ms)),
            str(r.prompt_tokens + r.completion_tokens),
            style=color,
        )

    console.print(table)

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    avg_score = sum(r.score for r in results) / total if total else 0.0
    total_tokens = sum(r.prompt_tokens + r.completion_tokens for r in results)
    console.print(
        f"[bold]{passed}/{total} passed[/bold]  "
        f"avg score [cyan]{avg_score:.2f}[/cyan]  "
        f"total tokens [cyan]{total_tokens}[/cyan]"
    )


def _write_snapshot(results: list[CaseResult], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".json"
    path = output_dir / filename
    data = [dataclasses.asdict(r) for r in results]
    path.write_text(json.dumps(data, indent=2))
    return path


def _load_result_json(path: Path) -> list[dict]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON in {path}:[/red] {e}")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def run(
    suite: Annotated[Path, typer.Argument(help="Path to eval suite YAML", exists=True)],
    model: Annotated[str, typer.Option(help="Model name")] = "gpt-4o-mini",
    output_dir: Annotated[Path, typer.Option(help="Directory for JSON results")] = Path("results"),
    base_url: Annotated[str | None, typer.Option(help="Override OpenAI base URL")] = None,
) -> None:
    """Run an eval suite against a model."""
    try:
        loaded_suite = load_suite(suite)
    except (ValueError, FileNotFoundError) as e:
        typer.echo(f"Error loading suite: {e}", err=True)
        raise typer.Exit(1)

    client_kwargs: dict = {}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = openai.OpenAI(**client_kwargs)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task(
            f"Running {len(loaded_suite.cases)} cases against [bold]{model}[/bold]…",
            total=None,
        )
        results = run_suite(loaded_suite, model, client)

    _print_table(results, loaded_suite.suite, model)

    snapshot_path = _write_snapshot(results, output_dir)
    console.print(f"\nResults written to [bold]{snapshot_path}[/bold]")


@app.command()
def diff(
    run_a: Annotated[Path, typer.Argument(help="Baseline result JSON")],
    run_b: Annotated[Path, typer.Argument(help="New result JSON")],
) -> None:
    """Diff two result snapshots."""
    data_a = _load_result_json(run_a)
    data_b = _load_result_json(run_b)

    by_id_a = {r["id"]: r for r in data_a}
    by_id_b = {r["id"]: r for r in data_b}
    all_ids = list(by_id_a.keys()) + [k for k in by_id_b if k not in by_id_a]

    table = Table(
        title=f"Diff: {run_a.name}  →  {run_b.name}",
        show_lines=False,
    )
    table.add_column("ID", style="bold")
    table.add_column("Score A", justify="right")
    table.add_column("Score B", justify="right")
    table.add_column("Δ Score", justify="right")
    table.add_column("Pass A", justify="center")
    table.add_column("Pass B", justify="center")
    table.add_column("Status")

    counts = {"REGRESSED": 0, "IMPROVED": 0, "UNCHANGED": 0, "NEW": 0, "REMOVED": 0}

    for case_id in all_ids:
        a = by_id_a.get(case_id)
        b = by_id_b.get(case_id)

        if a is None:
            status = "NEW"
            row_style = "green"
            score_a_str = "—"
            score_b_str = f"{b['score']:.2f}"
            delta_str = "—"
            pass_a_str = "—"
            pass_b_str = "✓" if b["passed"] else "✗"
        elif b is None:
            status = "REMOVED"
            row_style = "dim"
            score_a_str = f"{a['score']:.2f}"
            score_b_str = "—"
            delta_str = "—"
            pass_a_str = "✓" if a["passed"] else "✗"
            pass_b_str = "—"
        else:
            delta = b["score"] - a["score"]
            delta_str = f"{delta:+.2f}"
            score_a_str = f"{a['score']:.2f}"
            score_b_str = f"{b['score']:.2f}"
            pass_a_str = "✓" if a["passed"] else "✗"
            pass_b_str = "✓" if b["passed"] else "✗"
            if delta < 0:
                status = "REGRESSED"
                row_style = "red"
            elif delta > 0:
                status = "IMPROVED"
                row_style = "green"
            else:
                status = "UNCHANGED"
                row_style = "dim"

        counts[status] += 1
        table.add_row(
            case_id,
            score_a_str,
            score_b_str,
            delta_str,
            pass_a_str,
            pass_b_str,
            status,
            style=row_style,
        )

    console.print(table)
    console.print(
        f"[green]improved: {counts['IMPROVED']}[/green]  "
        f"[red]regressed: {counts['REGRESSED']}[/red]  "
        f"unchanged: {counts['UNCHANGED']}  "
        f"new: {counts['NEW']}  "
        f"removed: {counts['REMOVED']}"
    )


if __name__ == "__main__":
    app()
