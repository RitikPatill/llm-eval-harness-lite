import typer

app = typer.Typer(help="LLM Eval Harness Lite — the pytest of LLM outputs.")


@app.command()
def run(
    suite: str,
    model: str = "gpt-4o-mini",
    output_dir: str = "results",
):
    """Run an eval suite against a model."""
    typer.echo(f"[stub] run {suite} with {model} → {output_dir}")


@app.command()
def diff(run_a: str, run_b: str):
    """Diff two result snapshots."""
    typer.echo(f"[stub] diff {run_a} vs {run_b}")


if __name__ == "__main__":
    app()
