from datetime import datetime

from pydantic import BaseModel


class PredictionMilestoneOut(BaseModel):
    milestone_key: str
    achieved_at: datetime

    model_config = {"from_attributes": True}
