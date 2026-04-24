from app.schemas.match import ExpertPrediction

HOST_NATIONS = {"MEX", "USA", "CAN"}


def generate_expert_prediction(
    home_ranking: int | None,
    away_ranking: int | None,
    home_code: str | None = None,
    away_code: str | None = None,
) -> ExpertPrediction | None:
    """Predict a scoreline from FIFA rankings.

    Most World Cup matches are on neutral ground, so only host nations
    (USA, Mexico, Canada) receive a home-advantage goal boost.

    Voice-driven colour (Cantona, Zlatan, Hudson, etc.) lives in fun_comment
    / Expert Commentary on each match — this stays a plain score suggestion.
    """
    if home_ranking is None or away_ranking is None:
        return None

    home_rating = _ranking_to_rating(home_ranking)
    away_rating = _ranking_to_rating(away_ranking)

    diff = (home_rating - away_rating) / 350

    home_xg = max(0.1, 1.3 + diff * 0.7)
    away_xg = max(0.1, 1.3 - diff * 0.7)

    if home_code in HOST_NATIONS:
        home_xg += 0.3
    if away_code in HOST_NATIONS:
        away_xg += 0.3

    home_goals = _to_goals(home_xg)
    away_goals = _to_goals(away_xg)

    label = f"{home_goals}-{away_goals}"
    return ExpertPrediction(home_goals=home_goals, away_goals=away_goals, label=label)


def _ranking_to_rating(ranking: int) -> float:
    """Map FIFA ranking to an Elo-style rating (higher = better)."""
    return 2200 - 15 * max(1, ranking)


def _to_goals(xg: float) -> int:
    """Round expected goals with a 0.45 threshold to avoid excessive draws."""
    floor = int(xg)
    return floor + 1 if (xg - floor) >= 0.45 else floor
