import json
from pathlib import Path

import yaml

from notebook_report.classifier import ALL_LABELS
from notebook_report.parser import Cell


def _cell_to_dict(cell: Cell) -> dict:
    return {
        "id": cell.id,
        "cell_type": cell.cell_type,
        "execution_count": cell.execution_count,
        "source": cell.source,
        "outputs": json.loads(json.dumps(cell.outputs)),
        "stale": cell.stale,
        "reason": cell.reason,
        "label": cell.proposed_label,
        "gloss": cell.proposed_gloss,
    }


def write_review(cells: list[Cell], path: Path) -> None:
    data = {"cells": [_cell_to_dict(cell) for cell in cells]}
    Path(path).write_text(yaml.safe_dump(data, sort_keys=False))


def read_review(path: Path) -> list[Cell]:
    data = yaml.safe_load(Path(path).read_text()) or {}
    cells = []
    for entry in data.get("cells", []):
        label = entry.get("label")
        if label is not None and label not in ALL_LABELS:
            raise ValueError(f"review.yaml: cell {entry.get('id')!r} has unknown label {label!r}")
        cells.append(
            Cell(
                id=entry["id"],
                source=entry["source"],
                cell_type=entry["cell_type"],
                outputs=entry.get("outputs", []),
                execution_count=entry.get("execution_count"),
                stale=entry.get("stale", False),
                reason=entry.get("reason"),
                proposed_label=label,
                proposed_gloss=entry.get("gloss"),
            )
        )
    return cells
