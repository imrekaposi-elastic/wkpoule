"""Unit tests for knockout bracket resolution."""

from app.models.user import User
from app.schemas.ranking import GroupStanding, GroupTable
from app.services.annex_c import annex_lookup
from app.services.bracket_resolver import build_r32_from_annex, compute_predicted_knockout_teams


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
