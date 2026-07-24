import hashlib
import json
import re
from pathlib import Path

from notebook_report.parser import Cell


def _normalize(source: str) -> str:
    return re.sub(r"\s+", " ", source).strip()


def _hash_source(source: str) -> str:
    return hashlib.sha256(_normalize(source).encode("utf-8")).hexdigest()


def annotate_staleness(cells: list[Cell], cache_path: str | Path) -> list[Cell]:
    cache_path = Path(cache_path)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    for cell in cells:
        current_hash = _hash_source(cell.source)
        previous_hash = cache.get(cell.id)
        if previous_hash is not None and previous_hash != current_hash:
            cell.stale = True
            cell.reason = "source changed since the output was last recorded"
        else:
            cell.stale = False
            cell.reason = None
        cache[cell.id] = current_hash

    cache_path.write_text(json.dumps(cache, indent=2))
    return cells
