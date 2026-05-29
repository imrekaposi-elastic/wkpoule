"""Subgroup membership applications (user applies, admin approves)."""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.subgroup import SubgroupJoinRequest, SubgroupMember, SubgroupMessage
from app.models.user import User


def _max_message_id(db: Session, subgroup_id: int) -> int | None:
    return (
        db.query(func.max(SubgroupMessage.id))
        .filter(SubgroupMessage.subgroup_id == subgroup_id)
        .scalar()
    )


def approve_join_request(
    db: Session,
    request: SubgroupJoinRequest,
    admin_user_id: int,
) -> SubgroupMember:
    """Add member and mark request approved."""
    request.status = "approved"
    request.decided_at = datetime.now(timezone.utc)
    request.decided_by_user_id = admin_user_id

    existing = (
        db.query(SubgroupMember)
        .filter(
            SubgroupMember.subgroup_id == request.subgroup_id,
            SubgroupMember.user_id == request.user_id,
        )
        .first()
    )
    if existing:
        return existing

    member = SubgroupMember(
        subgroup_id=request.subgroup_id,
        user_id=request.user_id,
        role="member",
        last_read_message_id=_max_message_id(db, request.subgroup_id),
    )
    db.add(member)
    return member


def reject_join_request(
    db: Session,
    request: SubgroupJoinRequest,
    admin_user_id: int,
) -> None:
    request.status = "rejected"
    request.decided_at = datetime.now(timezone.utc)
    request.decided_by_user_id = admin_user_id


def pending_request_for_user(
    db: Session, subgroup_id: int, user_id: int
) -> SubgroupJoinRequest | None:
    return (
        db.query(SubgroupJoinRequest)
        .filter(
            SubgroupJoinRequest.subgroup_id == subgroup_id,
            SubgroupJoinRequest.user_id == user_id,
            SubgroupJoinRequest.status == "pending",
        )
        .first()
    )


def membership_status_for_user(
    db: Session, subgroup_id: int, user_id: int
) -> str:
    """none | member | admin | application_pending"""
    m = (
        db.query(SubgroupMember)
        .filter(
            SubgroupMember.subgroup_id == subgroup_id,
            SubgroupMember.user_id == user_id,
        )
        .first()
    )
    if m:
        return "admin" if m.role == "admin" else "member"
    if pending_request_for_user(db, subgroup_id, user_id):
        return "application_pending"
    return "none"
