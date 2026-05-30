from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.username import normalize_username

SupportedLanguage = Literal["en", "nl", "pt", "de", "he", "it", "es"]


def _normalize_username_field(value: object) -> object:
    if isinstance(value, str):
        return normalize_username(value)
    return value


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    preferred_language: SupportedLanguage = "en"

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> object:
        return _normalize_username_field(value)


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> object:
        return _normalize_username_field(value)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class SelfServicePasswordResetIn(BaseModel):
    """Reset password when username and email match the account (no email sent)."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> object:
        return _normalize_username_field(value)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    preferred_language: str

    model_config = {"from_attributes": True}


class UserLanguageIn(BaseModel):
    language: SupportedLanguage
