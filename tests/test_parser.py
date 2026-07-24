from pathlib import Path

from notebook_report.parser import parse_notebook

FIXTURE = Path(__file__).parent / "fixtures" / "out_of_order.ipynb"


def test_parse_orders_by_execution_count_and_strips_empty_cells():
    cells = parse_notebook(str(FIXTURE))

    assert [c.source for c in cells] == ["x = 1\nprint(x)", "x = 2\nprint(x)"]
    assert [c.execution_count for c in cells] == [1, 2]
    assert all(c.source.strip() for c in cells)
