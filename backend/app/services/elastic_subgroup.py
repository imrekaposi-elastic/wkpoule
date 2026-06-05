"""Auto-membership in the company Elastic subgroup for @elastic.co accounts."""

from __future__ import annotations

import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.subgroup import Subgroup, SubgroupMember
from app.models.user import User

logger = logging.getLogger(__name__)

ELASTIC_SUBGROUP_NAME = "Elastic"
ELASTIC_EMAIL_SUFFIX = "@elastic.co"
ELASTIC_SUBGROUP_ADMIN_USERNAMES = frozenset({"imre.kaposi"})


def is_elastic_email(email: str) -> bool:
    return (email or "").strip().lower().endswith(ELASTIC_EMAIL_SUFFIX)


def _elastic_subgroup_role(username: str) -> str:
    if username.strip().lower() in ELASTIC_SUBGROUP_ADMIN_USERNAMES:
        return "admin"
    return "member"


def _get_elastic_subgroup(db: Session) -> Subgroup | None:
    return (
        db.query(Subgroup)
        .filter(func.lower(Subgroup.name) == ELASTIC_SUBGROUP_NAME.lower())
        .first()
    )


def ensure_elastic_subgroup_admins(db: Session) -> None:
    """Promote configured usernames to admin in the Elastic subgroup (idempotent)."""
    sg = _get_elastic_subgroup(db)
    if sg is None:
        return
    for username in ELASTIC_SUBGROUP_ADMIN_USERNAMES:
        user = db.query(User).filter(func.lower(User.username) == username.lower()).first()
        if user is None:
            continue
        member = (
            db.query(SubgroupMember)
            .filter(
                SubgroupMember.subgroup_id == sg.id,
                SubgroupMember.user_id == user.id,
            )
            .first()
        )
        if member is None:
            db.add(
                SubgroupMember(
                    subgroup_id=sg.id,
                    user_id=user.id,
                    role="admin",
                )
            )
            logger.info(
                "Added %r as admin to subgroup %r",
                user.username,
                ELASTIC_SUBGROUP_NAME,
            )
            continue
        if member.role != "admin":
            member.role = "admin"
            logger.info(
                "Promoted %r to admin in subgroup %r",
                user.username,
                ELASTIC_SUBGROUP_NAME,
            )
    db.commit()


def add_user_to_elastic_subgroup(db: Session, user: User) -> None:
    """Add user to the Elastic subgroup when they register with an @elastic.co address."""
    if not is_elastic_email(user.email):
        return

    sg = _get_elastic_subgroup(db)
    if sg is None:
        sg = Subgroup(name=ELASTIC_SUBGROUP_NAME, created_by_user_id=user.id)
        db.add(sg)
        db.flush()
        logger.info("Created subgroup %r for first @elastic.co registrant", ELASTIC_SUBGROUP_NAME)

    exists = (
        db.query(SubgroupMember)
        .filter(
            SubgroupMember.subgroup_id == sg.id,
            SubgroupMember.user_id == user.id,
        )
        .first()
    )
    if exists:
        if (
            exists.role != "admin"
            and _elastic_subgroup_role(user.username) == "admin"
        ):
            exists.role = "admin"
            logger.info(
                "Promoted user_id=%s to admin in subgroup %r",
                user.id,
                ELASTIC_SUBGROUP_NAME,
            )
        return

    db.add(
        SubgroupMember(
            subgroup_id=sg.id,
            user_id=user.id,
            role=_elastic_subgroup_role(user.username),
        )
    )
    logger.info("Added user_id=%s to subgroup %r", user.id, ELASTIC_SUBGROUP_NAME)
