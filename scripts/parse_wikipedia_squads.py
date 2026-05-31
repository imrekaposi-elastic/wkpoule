#!/usr/bin/env python3
"""Parse Wikipedia 2026 World Cup squads export into team_squads_data.py."""

from __future__ import annotations

import re
from pathlib import Path

WIKI_PATH = Path(__file__).resolve().parents[1] / "agent-tools" / "wiki-squads.txt"
OUT_PATH = Path(__file__).resolve().parents[1] / "backend" / "app" / "data" / "team_squads_data.py"

NAME_TO_CODE: dict[str, str] = {
    "Czech Republic": "CZE",
    "Mexico": "MEX",
    "South Africa": "RSA",
    "South Korea": "KOR",
    "Bosnia and Herzegovina": "BIH",
    "Canada": "CAN",
    "Qatar": "QAT",
    "Switzerland": "SUI",
    "Brazil": "BRA",
    "Haiti": "HAI",
    "Morocco": "MAR",
    "Scotland": "SCO",
    "Australia": "AUS",
    "Paraguay": "PAR",
    "Turkey": "TUR",
    "United States": "USA",
    "Curaçao": "CUW",
    "Ecuador": "ECU",
    "Germany": "GER",
    "Ivory Coast": "CIV",
    "Japan": "JPN",
    "Netherlands": "NED",
    "Sweden": "SWE",
    "Tunisia": "TUN",
    "Belgium": "BEL",
    "Egypt": "EGY",
    "Iran": "IRN",
    "New Zealand": "NZL",
    "Cape Verde": "CPV",
    "Saudi Arabia": "KSA",
    "Spain": "ESP",
    "Uruguay": "URU",
    "France": "FRA",
    "Iraq": "IRQ",
    "Norway": "NOR",
    "Senegal": "SEN",
    "Algeria": "ALG",
    "Argentina": "ARG",
    "Austria": "AUT",
    "Jordan": "JOR",
    "Colombia": "COL",
    "DR Congo": "COD",
    "Portugal": "POR",
    "Uzbekistan": "UZB",
    "Croatia": "CRO",
    "England": "ENG",
    "Ghana": "GHA",
    "Panama": "PAN",
}

POS_MAP = {"1 GK": "GK", "2 DF": "DF", "3 MF": "MF", "4 FW": "FW"}

ROW_RE = re.compile(
    r"^\|\s*(?:(\d+)\s*\|)?\s*(1 GK|2 DF|3 MF|4 FW)\s*\|\s*"
    r"(.+?)\s*\|\s*\([^)]+\)[^|]*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*$"
)


def _clean_name(raw: str) -> str:
    name = raw.replace("(captain)", "").strip()
    name = re.sub(r"\[\d+\]", "", name).strip()
    return name


def parse_players(text: str, country: str) -> list[dict]:
    players: list[dict] = []
    sort_order = 0
    for line in text.splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        num_str, pos_key, name_raw, caps, _goals, club = m.groups()
        name = _clean_name(name_raw)
        club = club.strip()
        pos = POS_MAP[pos_key]
        shirt = int(num_str) if num_str else sort_order + 1
        players.append(
            {
                "name": name,
                "position": pos,
                "shirt_number": shirt,
                "club": club,
                "height_cm": 0,
                "weight_kg": 0,
                "caps": int(caps),
                "sort_order": sort_order,
            }
        )
        sort_order += 1
    return players


def main() -> None:
    wiki = Path(__file__).resolve().parents[2] / ".cursor" / "projects" / "c-Users-ImreKaposi-OneDrive-kaposi-net-Documenten-wkpoule" / "agent-tools" / "b0279c37-64dd-45dd-bafa-81a746f70f63.txt"
    if not wiki.exists():
        # fallback: copy path from repo if synced
        wiki = Path(__file__).resolve().parents[1] / "scripts" / "wiki-squads.txt"
    content = wiki.read_text(encoding="utf-8")

    sections = re.split(r"\n### ", content)
    squads: dict[str, list[dict]] = {}

    for section in sections[1:]:
        lines = section.splitlines()
        country = lines[0].strip()
        if country in ("Age", "Coach representation by country"):
            continue
        code = NAME_TO_CODE.get(country)
        if not code:
            continue
        players = parse_players(section, country)
        if players:
            squads[code] = players

    lines_out = [
        '"""Real player squads sourced from national team announcements (Wikipedia 2026 squads page)."""',
        "",
        "TEAM_SQUADS: dict[str, list[dict]] = {",
    ]
    for code in sorted(squads):
        lines_out.append(f'    "{code}": [')
        for p in squads[code]:
            lines_out.append(
                "        {"
                f'"name": {p["name"]!r}, '
                f'"position": {p["position"]!r}, '
                f'"shirt_number": {p["shirt_number"]}, '
                f'"club": {p["club"]!r}, '
                f'"height_cm": {p["height_cm"]}, '
                f'"weight_kg": {p["weight_kg"]}, '
                f'"caps": {p["caps"]}, '
                f'"sort_order": {p["sort_order"]}'
                "},"
            )
        lines_out.append("    ],")
    lines_out.append("}")
    lines_out.append("")

    OUT_PATH.write_text("\n".join(lines_out), encoding="utf-8")
    print(f"Wrote {len(squads)} squads to {OUT_PATH}")


if __name__ == "__main__":
    main()
