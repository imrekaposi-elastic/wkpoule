"""Unit tests for expert score suggestions."""

from app.services.expert import generate_expert_prediction


def test_generate_expert_prediction_returns_none_without_rankings():
    assert generate_expert_prediction(None, 10) is None


def test_generate_expert_prediction_favours_better_ranked_team():
    prediction = generate_expert_prediction(3, 40)

    assert prediction is not None
    assert prediction.home_goals >= prediction.away_goals


def test_generate_expert_prediction_boosts_host_nations():
    neutral = generate_expert_prediction(20, 20, home_code="NED", away_code="BRA")
    host = generate_expert_prediction(20, 20, home_code="USA", away_code="BRA")

    assert host.home_goals >= neutral.home_goals
