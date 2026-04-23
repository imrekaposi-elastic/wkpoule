"""FIFA World Cup 2026 Annex C — Round of 32 third-place routing (495 combinations).

Source: Wikipedia table «Combinations of matches in the round of 32», matching FIFA regulations.
Each row lists the eight groups whose third-placed teams qualify, then which third (3X) faces
which group winner slot (1Avs … 1Lvs → winners A,B,D,E,G,I,K,L respectively).
"""

from __future__ import annotations

from pathlib import Path

# Columns after the eight qualifying groups: third opponent for winners A,B,D,E,G,I,K,L
_WINNER_ORDER = ("A", "B", "D", "E", "G", "I", "K", "L")

_LOOKUP: dict[frozenset[str], dict[str, str]] | None = None


def _parse_row(line: str) -> tuple[frozenset[str], dict[str, str]] | None:
    line = line.strip()
    if not line.startswith("|") or line.startswith("|---"):
        return None
    parts = [p.strip() for p in line.split("|")]
    parts = [p for p in parts if p != ""]
    # parts[0]=scenario no, [1:9]=8 groups with advancing thirds, [9:17]=3E-style codes
    if len(parts) != 17:
        return None
    eight = parts[1:9]
    codes = parts[9:17]
    if len(set(eight)) != 8:
        return None
    assign: dict[str, str] = {}
    for w, code in zip(_WINNER_ORDER, codes):
        if len(code) != 2 or code[0] != "3":
            return None
        assign[w] = code[1].upper()
    return frozenset(eight), assign


def annex_lookup() -> dict[frozenset[str], dict[str, str]]:
    global _LOOKUP
    if _LOOKUP is not None:
        return _LOOKUP
    path = Path(__file__).resolve().parent.parent / "data" / "annex_c_wikipedia_lines.txt"
    raw = path.read_text(encoding="utf-8-sig")
    _LOOKUP = {}
    for line in raw.splitlines():
        if line.strip().startswith("##"):
            break
        parsed = _parse_row(line)
        if parsed is None:
            continue
        key, val = parsed
        _LOOKUP[key] = val
    if len(_LOOKUP) != 495:
        raise RuntimeError(f"Annex C load failed: expected 495 rows, got {len(_LOOKUP)}")
    return _LOOKUP
