"""Unit tests for matches router endpoints."""

from datetime import datetime, timezone
from unittest.mock import patch

from app.models.match import Match
from app.models.team import Team
from app.routers.matches import _match_matches_search, _match_to_out
from app.schemas.match import TeamOut
from tests.seed_fixtures import make_admin, seed_group_match, seed_knockout_match, seed_team, seed_venue


def test_list_matches_requires_auth(client):
    assert client.get("/api/matches").status_code == 401


def test_list_matches_empty(client, auth_headers):
    response = client.get("/api/matches", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_list_matches_with_filters(client, db, auth_headers):
    seed_group_match(db, match_number=101, group_letter="B", home_code="NED", away_code="BEL")

    by_group = client.get("/api/matches?group=B", headers=auth_headers)
    assert by_group.status_code == 200
    assert by_group.json()["total"] == 1

    by_search = client.get("/api/matches?search=ned", headers=auth_headers)
    assert by_search.status_code == 200
    assert by_search.json()["total"] == 1


def test_get_match_by_id(client, db, auth_headers):
    match = seed_group_match(db, match_number=102)

    response = client.get(f"/api/matches/{match.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["match_number"] == 102


def test_get_match_by_number(client, db, auth_headers):
    match = seed_group_match(db, match_number=103)

    response = client.get("/api/matches/by-number/103", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == match.id


def test_calendar_meta_and_by_day(client, db, auth_headers):
    seed_group_match(
        db,
        match_number=104,
        kickoff=datetime(2026, 6, 12, 15, 0, tzinfo=timezone.utc),
    )

    meta = client.get(
        "/api/matches/calendar-meta",
        params={"tz": "Europe/Amsterdam"},
        headers=auth_headers,
    )
    assert meta.status_code == 200
    assert meta.json()["first_match_local_date"]

    by_day = client.get(
        "/api/matches/by-day",
        params={"date": "2026-06-12", "tz": "Europe/Amsterdam"},
        headers=auth_headers,
    )
    assert by_day.status_code == 200
    assert len(by_day.json()) >= 1


def test_next_needing_prediction(client, db, auth_headers):
    seed_group_match(db, match_number=105)

    response = client.get(
        "/api/matches/next-needing-prediction",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() is not None


def test_admin_score_update(client, db, auth_headers):
    match = seed_group_match(db, match_number=106)
    make_admin(db)

    response = client.patch(
        f"/api/matches/{match.id}/score",
        headers=auth_headers,
        json={"home_score": 2, "away_score": 1, "status": "completed"},
    )
    assert response.status_code == 200
    assert response.json()["home_score"] == 2

    db.refresh(match)
    assert match.score_overridden_by_admin is True


def test_admin_knockout_draw_requires_winner(client, db, auth_headers):
    match = seed_knockout_match(db, match_number=109)
    make_admin(db)

    response = client.patch(
        f"/api/matches/{match.id}/score",
        headers=auth_headers,
        json={"home_score": 1, "away_score": 1, "status": "completed"},
    )
    assert response.status_code == 400


def test_admin_knockout_draw_saves_winner(client, db, auth_headers):
    match = seed_knockout_match(db, match_number=110)
    make_admin(db)
    home_id = match.home_team_id
    away_id = match.away_team_id

    response = client.patch(
        f"/api/matches/{match.id}/score",
        headers=auth_headers,
        json={
            "home_score": 2,
            "away_score": 2,
            "status": "completed",
            "winner_team_id": away_id,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["winner_team_id"] == away_id
    assert body["home_score"] == 2


def test_knockout_match_out_includes_bracket_slots(client, db, auth_headers):
    seed_knockout_match(
        db,
        match_number=89,
        home_code=None,
        away_code=None,
        kickoff=datetime(2026, 7, 5, 19, 0, tzinfo=timezone.utc),
    )
    make_admin(db)

    response = client.get("/api/matches?stage=round_of_16", headers=auth_headers)
    assert response.status_code == 200
    item = next(x for x in response.json()["items"] if x["match_number"] == 89)
    assert item["bracket_home_slot"] == "W74"
    assert item["bracket_away_slot"] == "W77"
    assert item["home_team"] is None


def test_match_matches_search_helpers(db):
    venue = seed_venue(db)
    home = seed_team(db, fifa_code="MEX", name="Mexico")
    away = seed_team(db, fifa_code="CAN", name="Canada")
    match = Match(
        id=1,
        match_number=1,
        stage="group",
        group_letter="A",
        venue_id=venue.id,
        kickoff_utc=datetime(2026, 6, 11, tzinfo=timezone.utc),
        status="upcoming",
        home_team_id=home.id,
        away_team_id=away.id,
    )
    match.home_team = home
    match.away_team = away
    match.venue = venue

    assert _match_matches_search(match, "") is True
    assert _match_matches_search(match, "mexico") is True
    assert _match_matches_search(match, "arena") is True
    assert _match_matches_search(match, "zzz") is False

    predicted = (
        TeamOut.model_validate(home),
        TeamOut.model_validate(away),
    )
    assert _match_matches_search(match, "can", predicted) is True

    out = _match_to_out(match, temperature=21.5)
    assert out.temperature_celsius == 21.5
    assert out.expert_prediction is not None


@patch("app.routers.matches.get_match_temperature", return_value=18.0)
def test_list_matches_with_predicted_teams(mock_temp, client, db, auth_headers):
    seed_group_match(db, match_number=107)

    response = client.get(
        "/api/matches",
        params={"predicted_teams": "true", "stage": "group"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1
    mock_temp.assert_not_called()
    for item in response.json()["items"]:
        assert item["temperature_celsius"] is None


@patch("app.routers.matches.get_match_temperature", return_value=18.0)
def test_get_match_by_id_still_fetches_weather(mock_temp, client, db, auth_headers):
    match = seed_group_match(db, match_number=108)

    response = client.get(f"/api/matches/{match.id}", headers=auth_headers)
    assert response.status_code == 200
    mock_temp.assert_called_once()
