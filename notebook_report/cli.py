from pathlib import Path

import click
import nbformat

from notebook_report.classifier import classify_cells
from notebook_report.parser import parse_notebook
from notebook_report.render import render_report
from notebook_report.review import read_review, write_review
from notebook_report.staleness import annotate_staleness


@click.group()
def main():
    pass


@main.command()
@click.argument("notebook_path")
def analyze(notebook_path):
    try:
        cells = parse_notebook(notebook_path)
    except (nbformat.reader.NotJSONError, nbformat.ValidationError) as exc:
        raise click.ClickException(f"Could not parse notebook {notebook_path!r}: {exc}")
    cache_path = Path(f"{Path(notebook_path).stem}.cache.json")
    cells = annotate_staleness(cells, cache_path)
    cells = classify_cells(cells)
    write_review(cells, Path("review.yaml"))
    click.echo("Wrote review.yaml")


@main.command()
@click.argument("review_path")
def render(review_path):
    cells = read_review(review_path)
    html = render_report(cells)
    Path("report.html").write_text(html)
    click.echo("Wrote report.html")


if __name__ == "__main__":
    main()
