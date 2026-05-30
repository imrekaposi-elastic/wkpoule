from sqlalchemy.orm import Session

from app.models.user import User


def normalize_username(username: str) -> str:
    return username.strip().lower()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == normalize_username(username)).first()
