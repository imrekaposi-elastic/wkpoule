import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import (
    _decode_token,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.username import get_user_by_username
from app.services.elastic_subgroup import add_user_to_elastic_subgroup
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    SelfServicePasswordResetIn,
    TokenResponse,
    UserLanguageIn,
    UserResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_username(db, body.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    email = str(body.email).strip().lower()
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=body.username,
        email=email,
        password_hash=hash_password(body.password),
        preferred_language=body.preferred_language,
        is_admin=False,
    )
    db.add(user)
    db.flush()
    add_user_to_elastic_subgroup(db, user)
    db.commit()
    db.refresh(user)
    logger.info(
        "%s registered",
        user.username,
        extra={
            "event.action": "user_register",
            "event.category": "authentication",
            "event.outcome": "success",
            "user.name": user.username,
            "user.id": user.id,
        },
    )
    return user


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def self_service_reset_password(
    body: SelfServicePasswordResetIn,
    db: Session = Depends(get_db),
):
    user = get_user_by_username(db, body.username)
    email_norm = body.email.strip().lower()
    if user is None or (user.email or "").strip().lower() != email_norm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or email",
        )
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return None


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = get_user_by_username(db, body.username)
    if not user or not verify_password(body.password, user.password_hash):
        client_ip = _client_ip(request)
        logger.info(
            "Failed login for %s",
            body.username,
            extra={
                "event.action": "user_login_failure",
                "event.category": "authentication",
                "event.outcome": "failure",
                "user.name": body.username,
                "client.ip": client_ip,
                "source.ip": client_ip,
            },
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    client_ip = _client_ip(request)
    logger.info(
        "%s has logged on successfully",
        user.username,
        extra={
            "event.action": "user_login",
            "event.category": "authentication",
            "event.outcome": "success",
            "user.name": user.username,
            "user.id": user.id,
            "client.ip": client_ip,
            "source.ip": client_ip,
        },
    )
    return TokenResponse(
        access_token=create_access_token(user.username),
        refresh_token=create_refresh_token(user.username),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    token_username = _decode_token(body.refresh_token, "refresh")
    user = get_user_by_username(db, token_username)
    canonical_username = user.username if user is not None else token_username
    extra = {
        "event.action": "session_refresh",
        "event.category": "authentication",
        "event.outcome": "success",
        "user.name": canonical_username,
    }
    if user is not None:
        extra["user.id"] = user.id
    logger.info(
        "%s has refreshed their session successfully",
        canonical_username,
        extra=extra,
    )
    return TokenResponse(
        access_token=create_access_token(canonical_username),
        refresh_token=create_refresh_token(canonical_username),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me/language", response_model=UserResponse)
def update_preferred_language(
    body: UserLanguageIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.preferred_language != body.language:
        user.preferred_language = body.language
        db.commit()
        db.refresh(user)
        logger.info(
            "%s updated preferred language",
            user.username,
            extra={
                "event.action": "user_language_update",
                "event.category": "user",
                "event.outcome": "success",
                "user.name": user.username,
                "user.id": user.id,
                "user.preferred_language": body.language,
            },
        )
    return user
