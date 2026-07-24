import json
from pathlib import Path

from notebook_report.parser import parse_notebook
from notebook_report.staleness import annotate_staleness

FIXTURE = Path(__file__).parent / "fixtures" / "staleness_base.ipynb"


def _write_notebook(path: Path, source_edits: dict[str, list[str]]):
    nb = json.loads(FIXTURE.read_text())
    for cell in nb["cells"]:
        if cell["id"] in source_edits:
            cell["source"] = source_edits[cell["id"]]
    path.write_text(json.dumps(nb))


def test_first_run_clean_then_edit_flags_only_the_edited_cell(tmp_path):
    nb_path = tmp_path / "notebook.ipynb"
    cache_path = tmp_path / "cache.json"
    _write_notebook(nb_path, {})

    first = annotate_staleness(parse_notebook(str(nb_path)), cache_path)
    assert [c.stale for c in first] == [False, False]
    assert cache_path.exists()

    _write_notebook(nb_path, {"cell-a": ["x = 999\n", "print(x)"]})
    second = annotate_staleness(parse_notebook(str(nb_path)), cache_path)

    stale_by_id = {c.id: c.stale for c in second}
    assert stale_by_id == {"cell-a": True, "cell-b": False}


def test_whitespace_only_edit_is_not_flagged_stale(tmp_path):
    nb_path = tmp_path / "notebook.ipynb"
    cache_path = tmp_path / "cache.json"
    _write_notebook(nb_path, {})
    annotate_staleness(parse_notebook(str(nb_path)), cache_path)

    _write_notebook(nb_path, {"cell-b": ["y   =   2\n", "print(y)  "]})
    second = annotate_staleness(parse_notebook(str(nb_path)), cache_path)

    stale_by_id = {c.id: c.stale for c in second}
    assert stale_by_id == {"cell-a": False, "cell-b": False}
