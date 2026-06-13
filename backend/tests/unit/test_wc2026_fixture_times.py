"""WC 2026 group-stage kickoffs aligned with football-data.org (2026-06-12)."""

from datetime import datetime, timezone

import pytest

from seed_data import GROUP_MATCHES

# Canonical UTC kickoffs from football-data.org v4 /competitions/WC/matches
CANONICAL_UTC: dict[tuple[str, str], str] = {
    ("MEX", "RSA"): "2026-06-11T19:00:00",
    ("KOR", "CZE"): "2026-06-12T02:00:00",
    ("CZE", "RSA"): "2026-06-18T16:00:00",
    ("MEX", "KOR"): "2026-06-19T01:00:00",
    ("CZE", "MEX"): "2026-06-25T01:00:00",
    ("RSA", "KOR"): "2026-06-25T01:00:00",
    ("CAN", "BIH"): "2026-06-12T19:00:00",
    ("QAT", "SUI"): "2026-06-13T19:00:00",
    ("SUI", "BIH"): "2026-06-18T19:00:00",
    ("CAN", "QAT"): "2026-06-18T22:00:00",
    ("SUI", "CAN"): "2026-06-24T19:00:00",
    ("BIH", "QAT"): "2026-06-24T19:00:00",
    ("BRA", "MAR"): "2026-06-13T22:00:00",
    ("HAI", "SCO"): "2026-06-14T01:00:00",
    ("SCO", "MAR"): "2026-06-19T22:00:00",
    ("BRA", "HAI"): "2026-06-20T00:30:00",
    ("SCO", "BRA"): "2026-06-24T22:00:00",
    ("MAR", "HAI"): "2026-06-24T22:00:00",
    ("USA", "PAR"): "2026-06-13T01:00:00",
    ("AUS", "TUR"): "2026-06-14T04:00:00",
    ("TUR", "PAR"): "2026-06-20T03:00:00",
    ("USA", "AUS"): "2026-06-19T19:00:00",
    ("TUR", "USA"): "2026-06-26T02:00:00",
    ("PAR", "AUS"): "2026-06-26T02:00:00",
    ("GER", "CUW"): "2026-06-14T17:00:00",
    ("CIV", "ECU"): "2026-06-14T23:00:00",
    ("GER", "CIV"): "2026-06-20T20:00:00",
    ("ECU", "CUW"): "2026-06-21T00:00:00",
    ("ECU", "GER"): "2026-06-25T20:00:00",
    ("CUW", "CIV"): "2026-06-25T20:00:00",
    ("NED", "JPN"): "2026-06-14T20:00:00",
    ("SWE", "TUN"): "2026-06-15T02:00:00",
    ("NED", "SWE"): "2026-06-20T17:00:00",
    ("TUN", "JPN"): "2026-06-21T04:00:00",
    ("TUN", "NED"): "2026-06-25T23:00:00",
    ("JPN", "SWE"): "2026-06-25T23:00:00",
    ("BEL", "EGY"): "2026-06-15T19:00:00",
    ("IRN", "NZL"): "2026-06-16T01:00:00",
    ("BEL", "IRN"): "2026-06-21T19:00:00",
    ("NZL", "EGY"): "2026-06-22T01:00:00",
    ("NZL", "BEL"): "2026-06-27T03:00:00",
    ("EGY", "IRN"): "2026-06-27T03:00:00",
    ("ESP", "CPV"): "2026-06-15T16:00:00",
    ("KSA", "URU"): "2026-06-15T22:00:00",
    ("ESP", "KSA"): "2026-06-21T16:00:00",
    ("URU", "CPV"): "2026-06-21T22:00:00",
    ("URU", "ESP"): "2026-06-27T00:00:00",
    ("CPV", "KSA"): "2026-06-27T00:00:00",
    ("FRA", "SEN"): "2026-06-16T19:00:00",
    ("IRQ", "NOR"): "2026-06-16T22:00:00",
    ("FRA", "IRQ"): "2026-06-22T21:00:00",
    ("NOR", "SEN"): "2026-06-23T00:00:00",
    ("NOR", "FRA"): "2026-06-26T19:00:00",
    ("SEN", "IRQ"): "2026-06-26T19:00:00",
    ("ARG", "ALG"): "2026-06-17T01:00:00",
    ("AUT", "JOR"): "2026-06-17T04:00:00",
    ("ARG", "AUT"): "2026-06-22T17:00:00",
    ("JOR", "ALG"): "2026-06-23T03:00:00",
    ("JOR", "ARG"): "2026-06-28T02:00:00",
    ("ALG", "AUT"): "2026-06-28T02:00:00",
    ("POR", "COD"): "2026-06-17T17:00:00",
    ("UZB", "COL"): "2026-06-18T02:00:00",
    ("POR", "UZB"): "2026-06-23T17:00:00",
    ("COL", "COD"): "2026-06-24T02:00:00",
    ("COL", "POR"): "2026-06-27T23:30:00",
    ("COD", "UZB"): "2026-06-27T23:30:00",
    ("ENG", "CRO"): "2026-06-17T20:00:00",
    ("GHA", "PAN"): "2026-06-17T23:00:00",
    ("ENG", "GHA"): "2026-06-23T20:00:00",
    ("PAN", "CRO"): "2026-06-23T23:00:00",
    ("PAN", "ENG"): "2026-06-27T21:00:00",
    ("CRO", "GHA"): "2026-06-27T21:00:00",
}


def test_group_stage_kickoffs_match_football_data_org():
    assert len(GROUP_MATCHES) == 72
    assert len(CANONICAL_UTC) == 72
    for spec in GROUP_MATCHES:
        pair = (spec["home"], spec["away"])
        expected = CANONICAL_UTC[pair]
        actual = spec["ko"].strftime("%Y-%m-%dT%H:%M:%S")
        assert actual == expected, f"mn{spec['mn']} {pair[0]} vs {pair[1]}"


def test_australia_turkey_is_june_14_utc():
    aus_tur = next(m for m in GROUP_MATCHES if m["home"] == "AUS" and m["away"] == "TUR")
    assert aus_tur["ko"] == datetime(2026, 6, 14, 4, 0, tzinfo=timezone.utc)
