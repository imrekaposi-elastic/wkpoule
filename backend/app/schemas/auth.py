from typing import Literal

from pydantic import BaseModel, EmailStr, Field

SupportedLanguage = Literal["en", "nl", "pt", "de", "he", "it", "es"]


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    preferred_language: SupportedLanguage = "en"


class LoginRequest(BaseModel):
    username: str
    password: str


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


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    preferred_language: str

    model_config = {"from_attributes": True}


class UserLanguageIn(BaseModel):
    language: SupportedLanguage
