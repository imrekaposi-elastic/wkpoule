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


def is_elastic_email(email: str) -> bool:
    return (email or "").strip().lower().endswith(ELASTIC_EMAIL_SUFFIX)


def add_user_to_elastic_subgroup(db: Session, user: User) -> None:
    """Add user to the Elastic subgroup when they register with an @elastic.co address."""
    if not is_elastic_email(user.email):
        return

    sg = (
        db.query(Subgroup)
        .filter(func.lower(Subgroup.name) == ELASTIC_SUBGROUP_NAME.lower())
        .first()
    )
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
        return

    db.add(
        SubgroupMember(
            subgroup_id=sg.id,
            user_id=user.id,
            role="member",
        )
    )
    logger.info("Added user_id=%s to subgroup %r", user.id, ELASTIC_SUBGROUP_NAME)
