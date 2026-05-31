"""Shared locale constants and profile flattening for team editorial content."""

from __future__ import annotations

PROFILE_FIELDS = ("qualification", "strengths", "weaknesses")
PROFILE_LANGUAGES = ("en", "nl", "pt", "de", "es", "it", "he")


def flatten_nested_profile(profile: dict) -> dict[str, str]:
    """Convert nested {field: {lang: text}} or flat {field_lang: text} to DB columns."""
    flat: dict[str, str] = {}
    for field in PROFILE_FIELDS:
        for lang in PROFILE_LANGUAGES:
            col = f"{field}_{lang}"
            if col in profile:
                flat[col] = profile[col]
                continue
            nested = profile.get(field)
            if isinstance(nested, dict) and lang in nested:
                flat[col] = nested[lang]
    return flat


def merge_locale_overlays(
    base: dict[str, dict[str, str]],
    *overlays: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Merge per-locale overlay dicts into flat column keys per FIFA code."""
    codes = set(base)
    for overlay in overlays:
        codes |= set(overlay)

    merged: dict[str, dict[str, str]] = {}
    for code in sorted(codes):
        flat: dict[str, str] = {}
        if code in base:
            flat.update(flatten_nested_profile(base[code]))
        for overlay in overlays:
            if code not in overlay:
                continue
            for key, value in overlay[code].items():
                flat[key] = value
        merged[code] = flat
    return merged
