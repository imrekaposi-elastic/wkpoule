from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.pagination import PaginatedResponse
from app.schemas.ranking import ParticipantRanking


class SubgroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class SubgroupMineOut(BaseModel):
    id: int
    name: str
    member_count: int
    my_role: str
    unread_message_count: int = 0


class SubgroupDirectoryOut(BaseModel):
    id: int
    name: str
    member_count: int
    membership_status: str  # none | member | admin | application_pending


class SubgroupJoinRequestOut(BaseModel):
    id: int
    subgroup_id: int
    subgroup_name: str
    user_id: int
    username: str
    created_at: datetime


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
    rankings: PaginatedResponse[ParticipantRanking]


class SubgroupInviteCreate(BaseModel):
    email: EmailStr


class SubgroupMessageCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


class SubgroupMessageOut(BaseModel):
    id: int
    user_id: int
    username: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}
