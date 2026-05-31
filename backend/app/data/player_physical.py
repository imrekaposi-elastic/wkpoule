"""Merge Wikidata height/weight onto squad player dicts."""

from __future__ import annotations

import unicodedata


def normalize_player_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFD", name)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in stripped.lower())
    return " ".join(cleaned.split())


def apply_physical_data(player: dict) -> dict:
    try:
        from app.data.player_physical_data import PHYSICAL_BY_NAME
    except ImportError:
        return player

    key = normalize_player_name(player["name"])
    physical = PHYSICAL_BY_NAME.get(key)
    if not physical:
        return player

    merged = dict(player)
    height = physical.get("height_cm")
    weight = physical.get("weight_kg")
    if height and not merged.get("height_cm"):
        merged["height_cm"] = height
    if weight and not merged.get("weight_kg"):
        merged["weight_kg"] = weight
    return merged
