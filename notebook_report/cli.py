from pathlib import Path

import click

from notebook_report.parser import parse_notebook
from notebook_report.render import render_report


@click.group()
def main():
    pass


@main.command()
@click.argument("notebook_path")
def analyze(notebook_path):
    raise NotImplementedError


@main.command()
@click.argument("notebook_path")
def render(notebook_path):
    cells = parse_notebook(notebook_path)
    html = render_report(cells)
    Path("report.html").write_text(html)
    click.echo("Wrote report.html")


if __name__ == "__main__":
    main()
