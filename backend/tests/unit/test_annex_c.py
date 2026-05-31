"""Unit tests for FIFA Annex C third-place routing table."""

from app.services.annex_c import annex_lookup


def test_annex_lookup_loads_all_combinations():
    table = annex_lookup()

    assert len(table) == 495
    sample_key = next(iter(table.keys()))
    assert len(sample_key) == 8
    assert set(table[sample_key].keys()) == {"A", "B", "D", "E", "G", "I", "K", "L"}


def test_annex_lookup_is_cached():
    assert annex_lookup() is annex_lookup()
