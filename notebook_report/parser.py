from dataclasses import dataclass, field
from typing import Any

import nbformat


@dataclass
class Cell:
    id: str
    source: str
    cell_type: str
    outputs: list[Any] = field(default_factory=list)
    execution_count: int | None = None


def parse_notebook(path: str) -> list[Cell]:
    nb = nbformat.read(path, as_version=4)

    numbered = [
        (
            original_index,
            Cell(
                id=raw.get("id", str(original_index)),
                source=raw.get("source", ""),
                cell_type=raw.get("cell_type", ""),
                outputs=raw.get("outputs", []),
                execution_count=raw.get("execution_count"),
            ),
        )
        for original_index, raw in enumerate(nb.cells)
        if raw.get("source", "").strip()
    ]

    numbered.sort(key=lambda pair: (pair[1].execution_count is None, pair[1].execution_count, pair[0]))
    return [cell for _, cell in numbered]
