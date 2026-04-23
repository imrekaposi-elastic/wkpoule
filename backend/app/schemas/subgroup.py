from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.ranking import ParticipantRanking


class SubgroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class SubgroupMineOut(BaseModel):
    id: int
    name: str
    member_count: int
    my_role: str
    unread_message_count: int = 0


class SubgroupInvitePendingOut(BaseModel):
    id: int
    subgroup_id: int
    subgroup_name: str
    email: str
    created_at: datetime


class SubgroupMemberBrief(BaseModel):
    user_id: int
    username: str
    role: str


class SubgroupDetailOut(BaseModel):
    id: int
    name: str
    my_role: str
    members: list[SubgroupMemberBrief]
    rankings: list[ParticipantRanking]


class SubgroupInviteCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)


class SubgroupMessageCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


class SubgroupMessageOut(BaseModel):
    id: int
    user_id: int
    username: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}
