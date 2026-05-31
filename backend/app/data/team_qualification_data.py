"""Load per-team qualification standings and match results from static JSON."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent / "qualification_groups.json"


@lru_cache(maxsize=1)
def _load_all() -> dict[str, dict]:
    with _DATA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_qualification_data(fifa_code: str) -> dict | None:
    """Return qualification JSON for a team, or None if unknown."""
    return _load_all().get(fifa_code.upper())
