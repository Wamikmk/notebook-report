import json
import re
from pathlib import Path

from click.testing import CliRunner

from notebook_report.cli import main
from notebook_report.parser import parse_notebook
from notebook_report.review import write_review
from notebook_report.staleness import annotate_staleness

FIXTURE = Path(__file__).parent / "fixtures" / "out_of_order.ipynb"
STALENESS_FIXTURE = Path(__file__).parent / "fixtures" / "staleness_base.ipynb"


def test_render_produces_ordered_html_with_source_and_output():
    runner = CliRunner()
    with runner.isolated_filesystem():
        cells = parse_notebook(str(FIXTURE))
        write_review(cells, Path("review.yaml"))

        result = runner.invoke(main, ["render", "review.yaml"])
        assert result.exit_code == 0, result.output

        html = Path("report.html").read_text()
        blocks = re.findall(r'<pre class="(source|output)">(.*?)</pre>', html, re.DOTALL)

        assert blocks == [
            ("source", "x = 1\nprint(x)"),
            ("output", "1\n"),
            ("source", "x = 2\nprint(x)"),
            ("output", "2\n"),
        ]


def _write_notebook(dest: Path, source_edits: dict[str, list[str]]):
    nb = json.loads(STALENESS_FIXTURE.read_text())
    for cell in nb["cells"]:
        if cell["id"] in source_edits:
            cell["source"] = source_edits[cell["id"]]
    dest.write_text(json.dumps(nb))


def test_render_shows_exactly_one_gap_box_for_the_edited_cell():
    runner = CliRunner()
    with runner.isolated_filesystem():
        nb_path = Path("notebook.ipynb")
        cache_path = Path("cache.json")
        _write_notebook(nb_path, {})

        cells = annotate_staleness(parse_notebook(str(nb_path)), cache_path)
        write_review(cells, Path("review.yaml"))
        first = runner.invoke(main, ["render", "review.yaml"])
        assert first.exit_code == 0, first.output
        assert "gap-box" not in Path("report.html").read_text()

        _write_notebook(nb_path, {"cell-a": ["x = 999\n", "print(x)"]})
        cells = annotate_staleness(parse_notebook(str(nb_path)), cache_path)
        write_review(cells, Path("review.yaml"))
        second = runner.invoke(main, ["render", "review.yaml"])
        assert second.exit_code == 0, second.output

        html = Path("report.html").read_text()
        gap_boxes = re.findall(r'<div class="gap-box" data-cell-id="([^"]+)">', html)
        assert gap_boxes == ["cell-a"]


def test_render_groups_cells_into_label_sections_in_canonical_order():
    runner = CliRunner()
    with runner.isolated_filesystem():
        cells = parse_notebook(str(FIXTURE))
        assert len(cells) == 2
        # Assign labels out of canonical order and include one unclassified
        # cell to confirm grouping, not document order, drives section layout.
        cells[0].proposed_label = "RESULT"
        cells[1].proposed_label = "SETUP"
        write_review(cells, Path("review.yaml"))

        result = runner.invoke(main, ["render", "review.yaml"])
        assert result.exit_code == 0, result.output

        html = Path("report.html").read_text()
        sections = re.findall(r'<section class="label-group" data-label="([^"]+)">', html)
        assert sections == ["Setup", "Result"]

        labels = re.findall(r'<span class="label">([^<]+)</span>', html)
        assert labels == ["SETUP", "RESULT"]
