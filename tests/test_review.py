import re
from pathlib import Path

import yaml
from click.testing import CliRunner

from notebook_report.cli import main
from notebook_report.parser import Cell

FIXTURE = Path(__file__).parent / "fixtures" / "out_of_order.ipynb"


def _fake_classify_cells(cells: list[Cell], client=None) -> list[Cell]:
    for cell in cells:
        cell.proposed_label = "EXPLORATION"
        cell.proposed_gloss = "stub gloss"
    return cells


def test_analyze_writes_review_yaml_and_render_reflects_hand_edited_label(monkeypatch):
    monkeypatch.setattr("notebook_report.cli.classify_cells", _fake_classify_cells)

    runner = CliRunner()
    with runner.isolated_filesystem():
        analyze_result = runner.invoke(main, ["analyze", str(FIXTURE)])
        assert analyze_result.exit_code == 0, analyze_result.output

        review_path = Path("review.yaml")
        assert review_path.exists()

        data = yaml.safe_load(review_path.read_text())
        assert [cell["label"] for cell in data["cells"]] == ["EXPLORATION", "EXPLORATION"]

        data["cells"][0]["label"] = "RESULT"
        review_path.write_text(yaml.safe_dump(data, sort_keys=False))

        render_result = runner.invoke(main, ["render", "review.yaml"])
        assert render_result.exit_code == 0, render_result.output

        html = Path("report.html").read_text()
        labels = re.findall(r'<span class="label">([^<]+)</span>', html)
        # M7 groups cells into sections in canonical SECTION_ORDER
        # (SETUP/EXPLORATION/RESULT/ABANDONED), not document order, so the
        # untouched EXPLORATION cell renders before the hand-edited RESULT cell.
        assert labels == ["EXPLORATION", "RESULT"]


def test_render_rejects_unknown_hand_edited_label():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("review.yaml").write_text(
            yaml.safe_dump(
                {
                    "cells": [
                        {
                            "id": "c1",
                            "cell_type": "code",
                            "execution_count": 1,
                            "source": "x = 1",
                            "outputs": [],
                            "stale": False,
                            "reason": None,
                            "label": "NOT_A_REAL_LABEL",
                            "gloss": None,
                        }
                    ]
                }
            )
        )
        result = runner.invoke(main, ["render", "review.yaml"])
        assert result.exit_code != 0
        assert "NOT_A_REAL_LABEL" in str(result.exception)


CORRUPT_FIXTURE = Path(__file__).parent / "fixtures" / "corrupt.ipynb"


def test_analyze_on_corrupt_notebook_fails_cleanly():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["analyze", str(CORRUPT_FIXTURE)])
        assert result.exit_code != 0
        assert "Could not parse notebook" in result.output
        assert "Traceback" not in result.output
