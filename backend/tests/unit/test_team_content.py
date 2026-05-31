"""Unit tests for applying editorial team content."""

from app.models.team import Team
from app.services.team_content import apply_team_content, backfill_all_teams


def _bare_team(fifa_code: str = "NED", name: str = "Netherlands") -> Team:
    return Team(
        name=name,
        fifa_code=fifa_code,
        group_letter="F",
        world_ranking=7,
        flag_url="https://example.com/ned.svg",
    )


def test_apply_team_content_populates_profile_players_and_qualification(db):
    team = _bare_team()
    db.add(team)
    db.flush()

    apply_team_content(db, team)
    db.commit()
    db.refresh(team)

    assert team.qualification_en
    assert team.strengths_nl
    assert team.qualification_data_json
    assert len(team.players) >= 20
    assert team.players[0].name
    assert team.players[0].position in {"GK", "DF", "MF", "FW"}


def test_backfill_all_teams_updates_every_row(db):
    db.add_all([_bare_team("NED"), _bare_team("BRA", "Brazil")])
    db.commit()

    backfill_all_teams(db)

    teams = db.query(Team).order_by(Team.fifa_code).all()
    assert len(teams) == 2
    assert all(team.qualification_en for team in teams)
    assert all(team.players for team in teams)
