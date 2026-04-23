from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.team import Team
from app.schemas.ranking import GroupStanding, GroupTable


def compute_group_standings(db: Session) -> list[GroupTable]:
    teams = db.query(Team).order_by(Team.group_letter, Team.world_ranking).all()
    completed_group_matches = (
        db.query(Match)
        .filter(Match.stage == "group", Match.status == "completed")
        .all()
    )

    team_stats: dict[int, dict] = {}
    for t in teams:
        team_stats[t.id] = {
            "team_id": t.id,
            "team_name": t.name,
            "fifa_code": t.fifa_code,
            "group_letter": t.group_letter,
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "goals_for": 0,
            "goals_against": 0,
            "points": 0,
            "h2h": {},
        }

    for m in completed_group_matches:
        if m.home_team_id is None or m.away_team_id is None:
            continue
        h = team_stats.get(m.home_team_id)
        a = team_stats.get(m.away_team_id)
        if h is None or a is None:
            continue

        h["played"] += 1
        a["played"] += 1
        h["goals_for"] += m.home_score
        h["goals_against"] += m.away_score
        a["goals_for"] += m.away_score
        a["goals_against"] += m.home_score

        if m.home_score > m.away_score:
            h["won"] += 1
            a["lost"] += 1
            h["points"] += 3
            h["h2h"].setdefault(m.away_team_id, 0)
            h["h2h"][m.away_team_id] += 3
            a["h2h"].setdefault(m.home_team_id, 0)
        elif m.home_score < m.away_score:
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

    result: list[GroupTable] = []
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
        # H2H tiebreaker for teams with equal points, GD, and GF
        _apply_h2h_tiebreaker(standings)

        result.append(
            GroupTable(
                group_letter=letter,
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
    return result


def _apply_h2h_tiebreaker(standings: list[dict]) -> None:
    """Re-sort tied teams by head-to-head points."""
    i = 0
    while i < len(standings):
        j = i + 1
        while j < len(standings) and _same_rank_key(standings[i], standings[j]):
            j += 1
        if j - i > 1:
            tied = standings[i:j]
            tied.sort(
                key=lambda s: max(s["h2h"].values()) if s["h2h"] else 0,
                reverse=True,
            )
            standings[i:j] = tied
        i = j


def _same_rank_key(a: dict, b: dict) -> bool:
    return (
        a["points"] == b["points"]
        and (a["goals_for"] - a["goals_against"]) == (b["goals_for"] - b["goals_against"])
        and a["goals_for"] == b["goals_for"]
    )
