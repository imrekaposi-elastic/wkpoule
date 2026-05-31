"""Provisional squad generator for Panini-style team pages (illustrative seed data)."""

from __future__ import annotations

import hashlib

POSITIONS = [
    ("GK", 1),
    ("DF", 2),
    ("DF", 3),
    ("DF", 4),
    ("DF", 5),
    ("MF", 6),
    ("MF", 8),
    ("MF", 10),
    ("FW", 7),
    ("FW", 9),
    ("FW", 11),
]

CLUB_POOLS: dict[str, list[str]] = {
    "uefa": [
        "Real Madrid", "Barcelona", "Bayern Munich", "Manchester City", "Arsenal",
        "Inter Milan", "AC Milan", "Juventus", "Paris Saint-Germain", "Liverpool",
        "Borussia Dortmund", "Napoli", "Benfica", "Ajax", "Porto",
    ],
    "conmebol": [
        "Flamengo", "Palmeiras", "River Plate", "Boca Juniors", "São Paulo",
        "Atlético Nacional", "Peñarol", "Independiente", "Corinthians", "Fluminense",
    ],
    "concacaf": [
        "LAFC", "Inter Miami", "Club América", "Monterrey", "Seattle Sounders",
        "Cruz Azul", "Toronto FC", "CF Monterrey", "New York City FC", "Tigres UANL",
    ],
    "caf": [
        "Al Ahly", "Wydad AC", "Mamelodi Sundowns", "Raja Casablanca", "Esperance",
        "Orlando Pirates", "Pyramids FC", "RS Berkane", "Simba SC", "TP Mazembe",
    ],
    "afc": [
        "Al Hilal", "Urawa Red Diamonds", "Melbourne City", "Al Nassr", "Jeonbuk Motors",
        "Persepolis", "Shanghai Port", "Ulsan HD", "Buriram United", "Al Duhail",
    ],
}

FIRST_NAMES = [
    "Alex", "Marco", "Lucas", "Diego", "Hugo", "Ivan", "Noah", "Leo", "Mateo", "Omar",
    "Yusuf", "Kenji", "Samir", "Felipe", "André", "Thomas", "Pierre", "Jan", "Erik", "Luis",
]

LAST_NAMES = [
    "Silva", "García", "Müller", "Rossi", "Dubois", "Jansen", "Okonkwo", "Tanaka",
    "Petrov", "Hernández", "Kowalski", "Ali", "Santos", "Nguyen", "Berg", "Costa",
    "Schmidt", "Moreau", "Fischer", "Reyes",
]

HOST_CODES = frozenset({"MEX", "USA", "CAN"})

CONFederation_BY_CODE: dict[str, str] = {
    "MEX": "concacaf", "USA": "concacaf", "CAN": "concacaf", "CUW": "concacaf",
    "HAI": "concacaf", "PAN": "concacaf",
    "BRA": "conmebol", "ARG": "conmebol", "COL": "conmebol", "URU": "conmebol",
    "ECU": "conmebol", "PAR": "conmebol",
    "RSA": "caf", "MAR": "caf", "CIV": "caf", "TUN": "caf", "EGY": "caf",
    "CPV": "caf", "SEN": "caf", "ALG": "caf", "COD": "caf", "GHA": "caf",
    "KOR": "afc", "QAT": "afc", "KSA": "afc", "IRN": "afc", "JPN": "afc",
    "AUS": "afc", "UZB": "afc", "JOR": "afc", "IRQ": "afc", "NZL": "afc",
}


def _confederation_pool(fifa_code: str) -> str:
    if fifa_code in HOST_CODES:
        return "concacaf"
    return CONFederation_BY_CODE.get(fifa_code, "uefa")


def _pick(items: list[str], seed: str, index: int) -> str:
    digest = hashlib.sha256(f"{seed}:{index}".encode()).hexdigest()
    return items[int(digest[:8], 16) % len(items)]


def build_team_squad(
    fifa_code: str,
    team_name: str,
    world_ranking: int,
) -> list[dict]:
    """Return 11 illustrative squad players for seed/backfill."""
    pool_key = _confederation_pool(fifa_code)
    clubs = CLUB_POOLS.get(pool_key, CLUB_POOLS["uefa"])
    seed = fifa_code
    rank_factor = max(1, min(world_ranking, 100))
    players: list[dict] = []

    for idx, (position, shirt_number) in enumerate(POSITIONS):
        first = _pick(FIRST_NAMES, seed, idx)
        last = _pick(LAST_NAMES, seed, idx + 11)
        club = _pick(clubs, seed, idx + 23)
        height = 172 + (int(_pick(list("0123456789"), seed, idx + 31), 16) % 23)
        weight = height - 75 + (idx % 5)
        base_caps = max(8, 120 - rank_factor)
        caps = base_caps + (idx * 3) + (int(_pick(list("0123456789"), seed, idx + 41), 16) % 25)

        players.append(
            {
                "name": f"{first} {last}",
                "position": position,
                "shirt_number": shirt_number,
                "club": club,
                "height_cm": height,
                "weight_kg": weight,
                "caps": caps,
                "sort_order": idx,
            }
        )

    return players
