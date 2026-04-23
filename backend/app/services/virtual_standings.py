"""Predicted group tables from the current user's scores (upcoming matches only)."""

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.team import Team
from app.schemas.ranking import GroupStanding, GroupTable
from app.services.group_rankings import _apply_h2h_tiebreaker

BEST_THIRD_SLOTS = 8  # Top 8 of 12 third-placed teams advance (2026 format)


def compute_virtual_group_standings(db: Session, user_id: int) -> list[GroupTable]:
    """Build group tables using this user's predicted scores for group-stage matches."""
    preds = (
        db.query(Prediction)
        .filter(Prediction.user_id == user_id)
        .all()
    )
    pred_by_match = {p.match_id: p for p in preds}

    teams = db.query(Team).order_by(Team.group_letter, Team.world_ranking).all()
    group_matches = (
        db.query(Match)
        .filter(Match.stage == "group")
        .order_by(Match.match_number)
        .all()
    )

    team_stats: dict[int, dict] = {}
    for t in teams:
        team_stats[t.id] = {
            "team_id": t.id,
            "team_name": t.name,
            "fifa_code": t.fifa_code,
            "group_letter": (t.group_letter or "").upper(),
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "goals_for": 0,
            "goals_against": 0,
            "points": 0,
            "h2h": {},
        }

    for m in group_matches:
        if m.home_team_id is None or m.away_team_id is None:
            continue
        p = pred_by_match.get(m.id)
        if p is None:
            continue
        hs, aws = p.home_score, p.away_score
        h = team_stats.get(m.home_team_id)
        a = team_stats.get(m.away_team_id)
        if h is None or a is None:
            continue

        h["played"] += 1
        a["played"] += 1
        h["goals_for"] += hs
        h["goals_against"] += aws
        a["goals_for"] += aws
        a["goals_against"] += hs

        if hs > aws:
            h["won"] += 1
            a["lost"] += 1
            h["points"] += 3
            h["h2h"].setdefault(m.away_team_id, 0)
            h["h2h"][m.away_team_id] += 3
            a["h2h"].setdefault(m.home_team_id, 0)
        elif hs < aws:
            a["won"] += 1
            h["lost"] += 1
            a["points"] += 3
            a["h2h"].setdefault(m.home_team_id, 0)
            a["h2h"][m.home_team_id] += 3
            h["h2h"].setdefault(m.away_team_id, 0)
        else:
            h["drawn"] += 1
            a["drawn"] += 1
            h["points"] += 1
            a["points"] += 1
            h["h2h"].setdefault(m.away_team_id, 0)
            h["h2h"][m.away_team_id] += 1
            a["h2h"].setdefault(m.home_team_id, 0)
            a["h2h"][m.home_team_id] += 1

    groups: dict[str, list[dict]] = {}
    for s in team_stats.values():
        groups.setdefault(s["group_letter"], []).append(s)

    tables: list[GroupTable] = []
    for letter in sorted(groups.keys()):
        standings = groups[letter]
        standings.sort(
            key=lambda s: (
                s["points"],
                s["goals_for"] - s["goals_against"],
                s["goals_for"],
            ),
            reverse=True,
        )
        _apply_h2h_tiebreaker(standings)

        tables.append(
            GroupTable(
                group_letter=letter.upper(),
                standings=[
                    GroupStanding(
                        team_id=s["team_id"],
                        team_name=s["team_name"],
                        fifa_code=s["fifa_code"],
                        played=s["played"],
                        won=s["won"],
                        drawn=s["drawn"],
                        lost=s["lost"],
                        goals_for=s["goals_for"],
                        goals_against=s["goals_against"],
                        goal_difference=s["goals_for"] - s["goals_against"],
                        points=s["points"],
                    )
                    for s in standings
                ],
            )
        )
    return tables


def best_third_place_team_ids(tables: list[GroupTable], top_n: int = BEST_THIRD_SLOTS) -> set[int]:
    """Which third-placed teams would advance among the best third-placers (WC 2026 style)."""
    thirds: list[tuple[int, int, int, int]] = []
    for gt in tables:
        if len(gt.standings) < 3:
            continue
        s = gt.standings[2]
        thirds.append((s.points, s.goal_difference, s.goals_for, s.team_id))
    thirds.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    return {t[3] for t in thirds[:top_n]}


def third_place_qualifies_for_group(gt: GroupTable, best_thirds: set[int]) -> bool | None:
    if len(gt.standings) < 3:
        return None
    return gt.standings[2].team_id in best_thirds
