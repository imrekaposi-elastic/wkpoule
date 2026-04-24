from datetime import datetime

from pydantic import BaseModel, Field


class AdminUserOut(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    preferred_language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserRoleIn(BaseModel):
    is_admin: bool


class AdminPasswordResetIn(BaseModel):
    """Admin sets a new password in-app (no email)."""

    new_password: str = Field(min_length=8, max_length=128)


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
