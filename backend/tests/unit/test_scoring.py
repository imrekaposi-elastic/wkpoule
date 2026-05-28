"""Unit tests for prediction scoring rules."""

import pytest

from app.services.scoring import calculate_points


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
def test_calculate_points(
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


def test_exact_score_includes_result_and_goal_bonuses():
    result = calculate_points(3, 2, 3, 2)

    assert result["points"] == 12
    assert result["correct_result"] is True
    assert result["correct_score"] is True
    assert result["correct_goal_count"] is True
