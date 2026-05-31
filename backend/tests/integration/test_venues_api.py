"""Integration tests for venues API."""

from app.models.venue import Venue


def test_list_venues_requires_auth(client):
    response = client.get("/api/venues")
    assert response.status_code == 401


def test_list_venues_returns_localized_reviews(client, db, auth_headers):
    db.add(
        Venue(
            name="Test Arena",
            city="Test City",
            country="USA",
            capacity=40000,
            latitude=40.0,
            longitude=-74.0,
            review_en="English review",
            review_nl="Nederlandse review",
            review_de="Deutsche review",
            accessibility_en="English access",
            accessibility_nl="Nederlandse access",
        )
    )
    db.commit()

    response = client.get("/api/venues", headers=auth_headers)

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["name"] == "Test Arena"
    assert rows[0]["review_en"] == "English review"
    assert rows[0]["review_de"] == "Deutsche review"
    assert rows[0]["matches"] == []


def test_get_venue_returns_404_for_unknown_id(client, auth_headers):
    response = client.get("/api/venues/9999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Venue not found"
