from datetime import datetime

from pydantic import BaseModel


class AdminUserOut(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserRoleIn(BaseModel):
    is_admin: bool


class AdminSubgroupMemberOut(BaseModel):
    user_id: int
    username: str
    role: str


class AdminSubgroupOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    member_count: int
    members: list[AdminSubgroupMemberOut]
