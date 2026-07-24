from types import SimpleNamespace

from notebook_report.classifier import classify_cells
from notebook_report.parser import Cell


class FakeClient:
    def __init__(self, responses):
        self._responses = iter(responses)
        self.messages = self

    def create(self, **kwargs):
        return next(self._responses)


def _tool_response(input_dict):
    return SimpleNamespace(content=[SimpleNamespace(type="tool_use", input=input_dict)])


def test_classify_cells_labels_unambiguous_cells_and_falls_back_on_malformed_response():
    setup_cell = Cell(
        id="c1",
        source="import pandas as pd\nimport numpy as np",
        cell_type="code",
        outputs=[],
        execution_count=1,
    )
    abandoned_cell = Cell(
        id="c2",
        source="# old approach, no longer used\n# df = load_old()",
        cell_type="code",
        outputs=[],
        execution_count=None,
    )
    broken_cell = Cell(id="c3", source="x = 1", cell_type="code", outputs=[], execution_count=2)

    responses = [
        _tool_response({"label": "SETUP", "gloss": "Imports pandas and numpy."}),
        _tool_response({"label": "ABANDONED", "gloss": "Old approach, commented out."}),
        _tool_response({"label": "NOT_A_LABEL", "gloss": "bad label value"}),
        _tool_response({"gloss": "missing the label field"}),
    ]
    client = FakeClient(responses)

    cells = classify_cells([setup_cell, abandoned_cell, broken_cell], client=client)

    assert cells[0].proposed_label == "SETUP"
    assert cells[0].proposed_gloss == "Imports pandas and numpy."
    assert cells[1].proposed_label == "ABANDONED"
    assert cells[1].proposed_gloss == "Old approach, commented out."
    assert cells[2].proposed_label == "UNCLASSIFIED"
    assert cells[2].proposed_gloss is None
