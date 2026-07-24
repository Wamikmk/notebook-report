from typing import Literal

import anthropic
from pydantic import BaseModel, ValidationError

from notebook_report.parser import Cell
from notebook_report.render import _output_text

MODEL = "claude-haiku-4-5-20251001"
TOOL_NAME = "classify_cell"
LABELS = ("SETUP", "EXPLORATION", "RESULT", "ABANDONED")
MAX_ATTEMPTS = 2

CLASSIFY_TOOL = {
    "name": TOOL_NAME,
    "description": "Propose a section label and a one-line gloss for a notebook cell.",
    "input_schema": {
        "type": "object",
        "properties": {
            "label": {"type": "string", "enum": list(LABELS)},
            "gloss": {"type": "string"},
        },
        "required": ["label", "gloss"],
    },
}


class CellClassification(BaseModel):
    label: Literal["SETUP", "EXPLORATION", "RESULT", "ABANDONED"]
    gloss: str


def _prompt(cell: Cell) -> str:
    output = _output_text(cell.outputs) or "(no output)"
    return (
        f"Cell type: {cell.cell_type}\n"
        f"Source:\n{cell.source}\n"
        f"Output:\n{output}\n\n"
        "Classify this notebook cell as one of SETUP, EXPLORATION, RESULT, or "
        "ABANDONED, and give a one-sentence gloss of what the cell does."
    )


def _request_classification(client: anthropic.Anthropic, cell: Cell) -> CellClassification:
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        tools=[CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[{"role": "user", "content": _prompt(cell)}],
    )
    tool_use = next(block for block in response.content if getattr(block, "type", None) == "tool_use")
    return CellClassification.model_validate(tool_use.input)


def classify_cell(cell: Cell, client: anthropic.Anthropic) -> Cell:
    for _ in range(MAX_ATTEMPTS):
        try:
            parsed = _request_classification(client, cell)
        except (ValidationError, StopIteration, AttributeError, TypeError, KeyError):
            continue
        cell.proposed_label = parsed.label
        cell.proposed_gloss = parsed.gloss
        return cell

    cell.proposed_label = "UNCLASSIFIED"
    cell.proposed_gloss = None
    return cell


def classify_cells(cells: list[Cell], client: anthropic.Anthropic | None = None) -> list[Cell]:
    client = client or anthropic.Anthropic()
    for cell in cells:
        classify_cell(cell, client)
    return cells
