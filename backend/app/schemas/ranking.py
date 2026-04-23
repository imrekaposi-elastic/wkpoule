from pydantic import BaseModel


class ParticipantRanking(BaseModel):
    rank: int
    user_id: int
    username: str
    total_points: int
    correct_results: int
    correct_scores: int
    correct_goal_counts: int
    predictions_made: int


class GroupStanding(BaseModel):
    team_id: int
    team_name: str
    fifa_code: str
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int


class GroupTable(BaseModel):
    group_letter: str
    standings: list[GroupStanding]


class VirtualGroupTable(BaseModel):
    """User's predicted group table; third_place_qualifies = would the 3rd team be a 'best third' (top 8 of 12)."""

    group_letter: str
    standings: list[GroupStanding]
    third_place_qualifies: bool | None = None
