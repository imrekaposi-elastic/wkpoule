"""Unit tests for knockout bracket resolution."""

from app.models.user import User
from app.schemas.ranking import GroupStanding, GroupTable
from app.services.annex_c import annex_lookup
from app.services.bracket_resolver import (
    R16_SOURCES,
    R32_STRUCTURE,
    build_r32_from_annex,
    compute_predicted_knockout_teams,
)

# FIFA 2026 regulations / Wikipedia knockout stage — Round of 32 match numbers 73–88.
OFFICIAL_R32_STRUCTURE: dict[int, tuple[tuple[str, str], tuple[str, str]]] = {
    73: (("2", "A"), ("2", "B")),
    74: (("1", "E"), ("3", "E")),
    75: (("1", "F"), ("2", "C")),
    76: (("1", "C"), ("2", "F")),
    77: (("1", "I"), ("3", "I")),
    78: (("2", "E"), ("2", "I")),
    79: (("1", "A"), ("3", "A")),
    80: (("1", "L"), ("3", "L")),
    81: (("1", "D"), ("3", "D")),
    82: (("1", "G"), ("3", "G")),
    83: (("2", "K"), ("2", "L")),
    84: (("1", "H"), ("2", "J")),
    85: (("1", "B"), ("3", "B")),
    86: (("1", "J"), ("2", "H")),
    87: (("1", "K"), ("3", "K")),
    88: (("2", "D"), ("2", "G")),
}


def test_r32_structure_matches_official_fifa_bracket():
    assert R32_STRUCTURE == OFFICIAL_R32_STRUCTURE


def test_r16_sources_match_official_fifa_bracket():
    assert R16_SOURCES == {
        89: (74, 77),
        90: (73, 75),
        91: (76, 78),
        92: (79, 80),
        93: (83, 84),
        94: (81, 82),
        95: (86, 88),
        96: (85, 87),
    }


def _standing(
    team_id: int,
    fifa_code: str,
    *,
    points: int = 9,
    goal_difference: int = 3,
    goals_for: int = 6,
) -> GroupStanding:
    return GroupStanding(
        team_id=team_id,
        team_name=fifa_code,
        fifa_code=fifa_code,
        played=3,
        won=3 if points == 9 else 1,
        drawn=0 if points == 9 else 1,
        lost=0,
        goals_for=goals_for,
        goals_against=goals_for - goal_difference,
        goal_difference=goal_difference,
        points=points,
    )


def test_build_r32_from_annex_resolves_known_slots():
    annex_row = annex_lookup()[frozenset({"A", "B", "C", "D", "E", "F", "G", "H"})]
    gt_by = {
        letter: GroupTable(
            group_letter=letter,
            standings=[
                _standing(team_id=100 + idx * 3, fifa_code=f"{letter}1"),
                _standing(
                    team_id=101 + idx * 3,
                    fifa_code=f"{letter}2",
                    points=6,
                    goal_difference=1,
                    goals_for=4,
                ),
                _standing(
                    team_id=102 + idx * 3,
                    fifa_code=f"{letter}3",
                    points=3,
                    goal_difference=0,
                    goals_for=3,
                ),
            ],
        )
        for idx, letter in enumerate("ABCDEFGH")
    }

    pairs, labels = build_r32_from_annex(gt_by, annex_row)

    assert pairs[73][0] == gt_by["A"].standings[1].team_id
    assert pairs[73][1] == gt_by["B"].standings[1].team_id
    assert labels[73] == ("A2", "B2")

    # Fixed runner-up / winner-vs-runner-up slots (no Annex lookup needed)
    assert labels[75] == ("F1", "C2")
    assert labels[76] == ("C1", "F2")
    assert labels[88] == ("D2", "G2")

    # Annex row 495: third-placed teams from groups A–H (see annex_c_wikipedia_lines.txt)
    assert labels[74] == ("E1", "C3")
    assert labels[79] == ("A1", "H3")
    assert labels[87] == ("K1", "D3")


def test_compute_predicted_knockout_teams_returns_bracket_labels(db):
    user = User(
        username="bracket",
        email="bracket@example.com",
        password_hash="x",
        preferred_language="en",
    )
    db.add(user)
    db.commit()

    teams, labels = compute_predicted_knockout_teams(db, user.id)

    assert labels[89] == ("W74", "W77")
    assert labels[104] == ("W101", "W102")
    assert teams[73] == (None, None)
