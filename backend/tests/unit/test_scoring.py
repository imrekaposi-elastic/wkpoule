"""Unit tests for prediction scoring rules."""

import pytest

from app.services.scoring import calculate_points

NED = 1
BRA = 2


@pytest.mark.parametrize(
    "pred_home,pred_away,actual_home,actual_away,expected_points,expected_result,expected_score,expected_goals",
    [
        (2, 1, 2, 1, 12, True, True, True),
        (1, 0, 2, 0, 3, True, False, False),
        (0, 0, 1, 1, 3, True, False, False),
        (3, 2, 1, 0, 3, True, False, False),
        (3, 2, 0, 1, 0, False, False, False),
        (2, 2, 1, 0, 0, False, False, False),
    ],
)
def test_calculate_points_group_stage(
    pred_home,
    pred_away,
    actual_home,
    actual_away,
    expected_points,
    expected_result,
    expected_score,
    expected_goals,
):
    result = calculate_points(pred_home, pred_away, actual_home, actual_away)

    assert result["points"] == expected_points
    assert result["correct_result"] is expected_result
    assert result["correct_score"] is expected_score
    assert result["correct_goal_count"] is expected_goals


def test_knockout_decided_in_90_uses_group_stage_scoring():
    result = calculate_points(2, 1, 2, 1, is_knockout=True)

    assert result["points"] == 12
    assert result["correct_result"] is True
    assert result["correct_score"] is True
    assert result["correct_goal_count"] is True


def test_knockout_non_draw_actual_uses_group_stage_scoring():
    """1-1 predicted, 0-2 after 90 — only goal-count bonus."""
    result = calculate_points(1, 1, 0, 2, is_knockout=True)

    assert result["points"] == 1
    assert result["correct_result"] is False
    assert result["correct_score"] is False
    assert result["correct_goal_count"] is True


def test_knockout_draw_after_90_exact_score_and_correct_winner():
    result = calculate_points(
        1,
        1,
        1,
        1,
        is_knockout=True,
        pred_advance_team_id=NED,
        actual_winner_team_id=NED,
    )

    assert result["points"] == 12
    assert result["correct_result"] is True
    assert result["correct_score"] is True
    assert result["correct_goal_count"] is True


def test_knockout_draw_after_90_exact_score_wrong_winner():
    result = calculate_points(
        1,
        1,
        1,
        1,
        is_knockout=True,
        pred_advance_team_id=BRA,
        actual_winner_team_id=NED,
    )

    assert result["points"] == 9
    assert result["correct_result"] is False
    assert result["correct_score"] is True
    assert result["correct_goal_count"] is True


def test_knockout_draw_after_90_correct_winner_without_exact_score():
    result = calculate_points(
        2,
        2,
        1,
        1,
        is_knockout=True,
        pred_advance_team_id=NED,
        actual_winner_team_id=NED,
    )

    assert result["points"] == 4
    assert result["correct_result"] is True
    assert result["correct_score"] is False
    assert result["correct_goal_count"] is False


def test_knockout_predicted_win_actual_draw_gets_nothing():
    result = calculate_points(
        2,
        1,
        1,
        1,
        is_knockout=True,
        pred_advance_team_id=None,
        actual_winner_team_id=NED,
    )

    assert result["points"] == 0
