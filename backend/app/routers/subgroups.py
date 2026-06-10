import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.cache.helpers import cached_call, run_cache_task
from app.cache.invalidation import invalidate_subgroup
from app.cache.keys import CacheKeys
from app.cache.ttl import SUBGROUPS_TTL
from app.auth import get_current_user
from app.database import get_db
from app.models.subgroup import (
    Subgroup,
    SubgroupInvite,
    SubgroupJoinRequest,
    SubgroupMember,
    SubgroupMessage,
)
from app.models.user import User
from app.schemas.pagination import paginate_list
from app.schemas.subgroup import (
    SubgroupCreate,
    SubgroupDetailOut,
    SubgroupDirectoryOut,
    SubgroupInviteCreate,
    SubgroupInvitePendingOut,
    SubgroupJoinRequestOut,
    SubgroupMemberBrief,
    SubgroupMessageCreate,
    SubgroupMessageOut,
    SubgroupMineOut,
)
from app.services.invite_email import send_subgroup_invite_email
from app.services.prediction_milestones import record_subgroup_message_milestone
from app.services.subgroup_join_requests import (
    approve_join_request,
    membership_status_for_user,
    pending_request_for_user,
    reject_join_request,
)
from app.services.subgroup_rankings import compute_participant_rankings

router = APIRouter()
logger = logging.getLogger("wkpoule.subgroups")

SUBGROUP_CHAT_MAX_MESSAGES = 256


def _invalidate_subgroup_cache(subgroup_id: int) -> None:
    run_cache_task(invalidate_subgroup(subgroup_id))

def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _get_member(db: Session, subgroup_id: int, user_id: int) -> SubgroupMember | None:
    return (
        db.query(SubgroupMember)
        .filter(
            SubgroupMember.subgroup_id == subgroup_id,
            SubgroupMember.user_id == user_id,
        )
        .first()
    )


def _unread_message_count(
    db: Session,
    subgroup_id: int,
    viewer_id: int,
    last_read_message_id: int | None,
) -> int:
    threshold = last_read_message_id or 0
    return int(
        db.query(func.count())
        .select_from(SubgroupMessage)
        .filter(
            SubgroupMessage.subgroup_id == subgroup_id,
            SubgroupMessage.id > threshold,
            SubgroupMessage.user_id != viewer_id,
        )
        .scalar()
        or 0
    )


def _trim_subgroup_messages_to_cap(db: Session, subgroup_id: int) -> None:
    """Keep at most SUBGROUP_CHAT_MAX_MESSAGES; delete oldest rows (FIFO)."""
    total = (
        db.query(func.count())
        .select_from(SubgroupMessage)
        .filter(SubgroupMessage.subgroup_id == subgroup_id)
        .scalar()
    )
    overflow = int(total or 0) - SUBGROUP_CHAT_MAX_MESSAGES
    if overflow <= 0:
        return
    oldest_ids = [
        row[0]
        for row in db.query(SubgroupMessage.id)
        .filter(SubgroupMessage.subgroup_id == subgroup_id)
        .order_by(SubgroupMessage.id.asc())
        .limit(overflow)
        .all()
    ]
    if oldest_ids:
        db.query(SubgroupMessage).filter(SubgroupMessage.id.in_(oldest_ids)).delete(
            synchronize_session=False
        )


@router.post("", response_model=SubgroupMineOut, status_code=status.HTTP_201_CREATED)
def create_subgroup(
    body: SubgroupCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sg = Subgroup(name=body.name.strip(), created_by_user_id=user.id)
    db.add(sg)
    db.flush()
    db.add(
        SubgroupMember(
            subgroup_id=sg.id,
            user_id=user.id,
            role="admin",
        )
    )
    db.commit()
    db.refresh(sg)
    return SubgroupMineOut(
        id=sg.id,
        name=sg.name,
        member_count=1,
        my_role="admin",
    )


@router.get("/mine", response_model=list[SubgroupMineOut])
def list_my_subgroups(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            SubgroupMember.subgroup_id,
            Subgroup.name,
            SubgroupMember.role,
            SubgroupMember.last_read_message_id,
        )
        .join(Subgroup, Subgroup.id == SubgroupMember.subgroup_id)
        .filter(SubgroupMember.user_id == user.id)
        .all()
    )
    out: list[SubgroupMineOut] = []
    for subgroup_id, name, role, last_read in rows:
        cnt = (
            db.query(func.count())
            .select_from(SubgroupMember)
            .filter(SubgroupMember.subgroup_id == subgroup_id)
            .scalar()
        )
        unread = _unread_message_count(db, subgroup_id, user.id, last_read)
        out.append(
            SubgroupMineOut(
                id=subgroup_id,
                name=name,
                member_count=int(cnt or 0),
                my_role=role,
                unread_message_count=unread,
            )
        )
    return sorted(out, key=lambda x: x.name.lower())


@router.get("/directory", response_model=list[SubgroupDirectoryOut])
def list_subgroup_directory(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """All subgroups with membership status for the current user."""
    subgroups = db.query(Subgroup).order_by(Subgroup.name).all()
    out: list[SubgroupDirectoryOut] = []
    for sg in subgroups:
        cnt = (
            db.query(func.count())
            .select_from(SubgroupMember)
            .filter(SubgroupMember.subgroup_id == sg.id)
            .scalar()
        )
        out.append(
            SubgroupDirectoryOut(
                id=sg.id,
                name=sg.name,
                member_count=int(cnt or 0),
                membership_status=membership_status_for_user(db, sg.id, user.id),
            )
        )
    return out


@router.get("/join-requests/incoming", response_model=list[SubgroupJoinRequestOut])
def list_incoming_join_requests(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pending membership applications for subgroups the current user administers."""
    admin_subgroup_ids = [
        row[0]
        for row in db.query(SubgroupMember.subgroup_id)
        .filter(
            SubgroupMember.user_id == user.id,
            SubgroupMember.role == "admin",
        )
        .all()
    ]
    if not admin_subgroup_ids:
        return []
    rows = (
        db.query(SubgroupJoinRequest, Subgroup.name, User.username)
        .join(Subgroup, Subgroup.id == SubgroupJoinRequest.subgroup_id)
        .join(User, User.id == SubgroupJoinRequest.user_id)
        .filter(
            SubgroupJoinRequest.subgroup_id.in_(admin_subgroup_ids),
            SubgroupJoinRequest.status == "pending",
        )
        .order_by(SubgroupJoinRequest.created_at.asc())
        .all()
    )
    return [
        SubgroupJoinRequestOut(
            id=req.id,
            subgroup_id=req.subgroup_id,
            subgroup_name=name,
            user_id=req.user_id,
            username=uname,
            created_at=req.created_at,
        )
        for req, name, uname in rows
    ]


@router.get("/invites/pending", response_model=list[SubgroupInvitePendingOut])
def list_pending_invites(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    email = _normalize_email(user.email)
    invites = (
        db.query(SubgroupInvite, Subgroup.name)
        .join(Subgroup, Subgroup.id == SubgroupInvite.subgroup_id)
        .filter(
            SubgroupInvite.email == email,
            SubgroupInvite.status == "pending",
        )
        .order_by(SubgroupInvite.created_at.desc())
        .all()
    )
    return [
        SubgroupInvitePendingOut(
            id=inv.id,
            subgroup_id=inv.subgroup_id,
            subgroup_name=name,
            email=inv.email,
            created_at=inv.created_at,
        )
        for inv, name in invites
    ]


@router.post("/invites/{invite_id}/accept", response_model=SubgroupMineOut)
def accept_invite(
    invite_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.query(SubgroupInvite).filter(SubgroupInvite.id == invite_id).first()
    if inv is None:
        raise HTTPException(status_code=404, detail="Invite not found")
    if inv.status != "pending":
        raise HTTPException(status_code=400, detail="Invite is no longer pending")
    if inv.expires_at and inv.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite has expired")
    if _normalize_email(user.email) != inv.email:
        raise HTTPException(status_code=403, detail="This invite is for a different email address")

    existing = _get_member(db, inv.subgroup_id, user.id)
    if existing:
        inv.status = "accepted"
        db.commit()
        sg = db.query(Subgroup).filter(Subgroup.id == inv.subgroup_id).first()
        cnt = (
            db.query(func.count())
            .select_from(SubgroupMember)
            .filter(SubgroupMember.subgroup_id == inv.subgroup_id)
            .scalar()
        )
        return SubgroupMineOut(
            id=sg.id,
            name=sg.name,
            member_count=int(cnt or 0),
            my_role=existing.role,
            unread_message_count=_unread_message_count(
                db, sg.id, user.id, existing.last_read_message_id
            ),
        )

    max_msg_id = (
        db.query(func.max(SubgroupMessage.id))
        .filter(SubgroupMessage.subgroup_id == inv.subgroup_id)
        .scalar()
    )
    inv.status = "accepted"
    db.add(
        SubgroupMember(
            subgroup_id=inv.subgroup_id,
            user_id=user.id,
            role="member",
            last_read_message_id=max_msg_id,
        )
    )
    db.commit()
    db.refresh(inv)
    sg = db.query(Subgroup).filter(Subgroup.id == inv.subgroup_id).first()
    cnt = (
        db.query(func.count())
        .select_from(SubgroupMember)
        .filter(SubgroupMember.subgroup_id == inv.subgroup_id)
        .scalar()
    )
    _invalidate_subgroup_cache(inv.subgroup_id)
    return SubgroupMineOut(
        id=sg.id,
        name=sg.name,
        member_count=int(cnt or 0),
        my_role="member",
    )


@router.post("/invites/{invite_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
def decline_invite(
    invite_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.query(SubgroupInvite).filter(SubgroupInvite.id == invite_id).first()
    if inv is None:
        raise HTTPException(status_code=404, detail="Invite not found")
    if _normalize_email(user.email) != inv.email:
        raise HTTPException(status_code=403, detail="This invite is for a different email address")
    if inv.status == "pending":
        inv.status = "declined"
        db.commit()
    return None


@router.post(
    "/{subgroup_id}/join-requests",
    response_model=SubgroupJoinRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def apply_for_membership(
    subgroup_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sg = db.query(Subgroup).filter(Subgroup.id == subgroup_id).first()
    if not sg:
        raise HTTPException(status_code=404, detail="Subgroup not found")
    if _get_member(db, subgroup_id, user.id):
        raise HTTPException(status_code=400, detail="You are already a member")
    pending = pending_request_for_user(db, subgroup_id, user.id)
    if pending:
        raise HTTPException(status_code=400, detail="You already have a pending application")

    prior = (
        db.query(SubgroupJoinRequest)
        .filter(
            SubgroupJoinRequest.subgroup_id == subgroup_id,
            SubgroupJoinRequest.user_id == user.id,
        )
        .first()
    )
    if prior and prior.status == "rejected":
        prior.status = "pending"
        prior.decided_at = None
        prior.decided_by_user_id = None
        prior.created_at = datetime.now(timezone.utc)
        req = prior
        db.commit()
        db.refresh(req)
    else:
        req = SubgroupJoinRequest(subgroup_id=subgroup_id, user_id=user.id, status="pending")
        db.add(req)
        db.commit()
        db.refresh(req)
    return SubgroupJoinRequestOut(
        id=req.id,
        subgroup_id=sg.id,
        subgroup_name=sg.name,
        user_id=user.id,
        username=user.username,
        created_at=req.created_at,
    )


@router.delete(
    "/{subgroup_id}/join-requests/mine",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cancel_my_join_request(
    subgroup_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = pending_request_for_user(db, subgroup_id, user.id)
    if req is None:
        raise HTTPException(status_code=404, detail="No pending application found")
    db.delete(req)
    db.commit()
    return None


@router.post(
    "/{subgroup_id}/join-requests/{request_id}/approve",
    response_model=SubgroupMineOut,
)
def approve_join_request_endpoint(
    subgroup_id: int,
    request_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    admin_m = _get_member(db, subgroup_id, user.id)
    if not admin_m or admin_m.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only subgroup admins can approve applications",
        )
    req = (
        db.query(SubgroupJoinRequest)
        .filter(
            SubgroupJoinRequest.id == request_id,
            SubgroupJoinRequest.subgroup_id == subgroup_id,
        )
        .first()
    )
    if req is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Application is no longer pending")

    approve_join_request(db, req, user.id)
    db.commit()

    sg = db.query(Subgroup).filter(Subgroup.id == subgroup_id).first()
    cnt = (
        db.query(func.count())
        .select_from(SubgroupMember)
        .filter(SubgroupMember.subgroup_id == subgroup_id)
        .scalar()
    )
    _invalidate_subgroup_cache(subgroup_id)
    return SubgroupMineOut(
        id=sg.id,
        name=sg.name,
        member_count=int(cnt or 0),
        my_role="admin",
        unread_message_count=_unread_message_count(
            db, subgroup_id, user.id, admin_m.last_read_message_id
        ),
    )


@router.post(
    "/{subgroup_id}/join-requests/{request_id}/reject",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reject_join_request_endpoint(
    subgroup_id: int,
    request_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    admin_m = _get_member(db, subgroup_id, user.id)
    if not admin_m or admin_m.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only subgroup admins can reject applications",
        )
    req = (
        db.query(SubgroupJoinRequest)
        .filter(
            SubgroupJoinRequest.id == request_id,
            SubgroupJoinRequest.subgroup_id == subgroup_id,
        )
        .first()
    )
    if req is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Application is no longer pending")

    reject_join_request(db, req, user.id)
    db.commit()
    return None


@router.get("/{subgroup_id}", response_model=SubgroupDetailOut)
async def get_subgroup_detail(
    subgroup_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=20),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = _get_member(db, subgroup_id, user.id)
    if not m:
        raise HTTPException(status_code=403, detail="Not a member of this subgroup")

    cache_key = CacheKeys.subgroup_detail(subgroup_id, user.id, page, page_size)

    def compute() -> SubgroupDetailOut:
        sg = db.query(Subgroup).filter(Subgroup.id == subgroup_id).first()
        if not sg:
            raise HTTPException(status_code=404, detail="Subgroup not found")

        member_ids = [
            row[0]
            for row in db.query(SubgroupMember.user_id)
            .filter(SubgroupMember.subgroup_id == subgroup_id)
            .all()
        ]
        all_rankings = compute_participant_rankings(db, member_ids)
        rankings = paginate_list(all_rankings, page, page_size)

        member_rows = (
            db.query(SubgroupMember.user_id, User.username, SubgroupMember.role)
            .join(User, User.id == SubgroupMember.user_id)
            .filter(SubgroupMember.subgroup_id == subgroup_id)
            .order_by(SubgroupMember.role.desc(), User.username)
            .all()
        )
        members = [
            SubgroupMemberBrief(user_id=uid, username=uname, role=role)
            for uid, uname, role in member_rows
        ]

        return SubgroupDetailOut(
            id=sg.id,
            name=sg.name,
            my_role=m.role,
            members=members,
            rankings=rankings,
        )

    return await cached_call(cache_key, SUBGROUPS_TTL, SubgroupDetailOut, compute)


@router.delete(
    "/{subgroup_id}/members/{member_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_subgroup_member(
    subgroup_id: int,
    member_user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    admin_m = _get_member(db, subgroup_id, user.id)
    if not admin_m or admin_m.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only subgroup admins can remove members",
        )
    if member_user_id == user.id:
        raise HTTPException(
            status_code=400,
            detail="Use leave to remove yourself from the subgroup",
        )
    target = _get_member(db, subgroup_id, member_user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Member not found in this subgroup")
    if target.role == "admin":
        raise HTTPException(
            status_code=400,
            detail="Cannot remove another subgroup admin",
        )
    db.delete(target)
    db.commit()
    _invalidate_subgroup_cache(subgroup_id)
    return None


@router.delete("/{subgroup_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subgroup(
    subgroup_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = _get_member(db, subgroup_id, user.id)
    if not m or m.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only subgroup admins can delete the subgroup",
        )
    sg = db.query(Subgroup).filter(Subgroup.id == subgroup_id).first()
    if not sg:
        raise HTTPException(status_code=404, detail="Subgroup not found")
    db.delete(sg)
    db.commit()
    return None


@router.post("/{subgroup_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_subgroup(
    subgroup_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = _get_member(db, subgroup_id, user.id)
    if not m:
        raise HTTPException(status_code=404, detail="Membership not found")

    sg = db.query(Subgroup).filter(Subgroup.id == subgroup_id).first()
    if not sg:
        raise HTTPException(status_code=404, detail="Subgroup not found")

    others = (
        db.query(SubgroupMember)
        .filter(
            SubgroupMember.subgroup_id == subgroup_id,
            SubgroupMember.user_id != user.id,
        )
        .all()
    )

    if not others:
        db.delete(sg)
        db.commit()
        return None

    if m.role == "admin" and not any(o.role == "admin" for o in others):
        # Sole admin leaving: delete the whole subgroup (all members, chat, invites)
        db.delete(sg)
        db.commit()
        return None

    db.delete(m)
    db.commit()
    _invalidate_subgroup_cache(subgroup_id)
    return None


@router.post("/{subgroup_id}/invites", response_model=SubgroupInvitePendingOut, status_code=status.HTTP_201_CREATED)
def create_invite(
    subgroup_id: int,
    body: SubgroupInviteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = _get_member(db, subgroup_id, user.id)
    if not m or m.role != "admin":
        raise HTTPException(status_code=403, detail="Only subgroup admins can invite")

    email = _normalize_email(str(body.email))
    if email == _normalize_email(user.email):
        raise HTTPException(status_code=400, detail="You cannot invite yourself")

    target_user = db.query(User).filter(func.lower(User.email) == email).first()
    if target_user:
        if _get_member(db, subgroup_id, target_user.id):
            raise HTTPException(status_code=400, detail="User is already a member")

    dup = (
        db.query(SubgroupInvite)
        .filter(
            SubgroupInvite.subgroup_id == subgroup_id,
            SubgroupInvite.email == email,
            SubgroupInvite.status == "pending",
        )
        .first()
    )
    if dup:
        raise HTTPException(status_code=400, detail="A pending invite already exists for this email")

    sg = db.query(Subgroup).filter(Subgroup.id == subgroup_id).first()
    if not sg:
        raise HTTPException(status_code=404, detail="Subgroup not found")

    inv = SubgroupInvite(
        subgroup_id=subgroup_id,
        email=email,
        invited_by_user_id=user.id,
        status="pending",
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    send_subgroup_invite_email(email, sg.name, user.username)

    return SubgroupInvitePendingOut(
        id=inv.id,
        subgroup_id=sg.id,
        subgroup_name=sg.name,
        email=inv.email,
        created_at=inv.created_at,
    )


@router.get("/{subgroup_id}/messages", response_model=list[SubgroupMessageOut])
def list_messages(
    subgroup_id: int,
    limit: int = SUBGROUP_CHAT_MAX_MESSAGES,
    before_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    member = _get_member(db, subgroup_id, user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this subgroup")
    total_msgs = (
        db.query(func.count())
        .select_from(SubgroupMessage)
        .filter(SubgroupMessage.subgroup_id == subgroup_id)
        .scalar()
    )
    if int(total_msgs or 0) > SUBGROUP_CHAT_MAX_MESSAGES:
        _trim_subgroup_messages_to_cap(db, subgroup_id)
        db.commit()
    limit = min(max(limit, 1), SUBGROUP_CHAT_MAX_MESSAGES)
    q = (
        db.query(SubgroupMessage, User.username)
        .join(User, User.id == SubgroupMessage.user_id)
        .filter(SubgroupMessage.subgroup_id == subgroup_id)
    )
    if before_id is not None:
        q = q.filter(SubgroupMessage.id < before_id)
    rows = q.order_by(SubgroupMessage.id.desc()).limit(limit).all()
    rows.reverse()

    max_in_thread = (
        db.query(func.max(SubgroupMessage.id))
        .filter(SubgroupMessage.subgroup_id == subgroup_id)
        .scalar()
    )
    if max_in_thread is not None and (
        member.last_read_message_id is None or member.last_read_message_id < max_in_thread
    ):
        member.last_read_message_id = max_in_thread
        db.add(member)
        db.commit()

    return [
        SubgroupMessageOut(
            id=msg.id,
            user_id=msg.user_id,
            username=uname,
            body=msg.body,
            created_at=msg.created_at,
        )
        for msg, uname in rows
    ]


@router.post("/{subgroup_id}/messages", response_model=SubgroupMessageOut, status_code=status.HTTP_201_CREATED)
def post_message(
    subgroup_id: int,
    body: SubgroupMessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not _get_member(db, subgroup_id, user.id):
        raise HTTPException(status_code=403, detail="Not a member of this subgroup")
    msg = SubgroupMessage(
        subgroup_id=subgroup_id,
        user_id=user.id,
        body=body.body.strip(),
    )
    db.add(msg)
    db.flush()
    _trim_subgroup_messages_to_cap(db, subgroup_id)
    poster = _get_member(db, subgroup_id, user.id)
    if poster:
        poster.last_read_message_id = msg.id
        db.add(poster)
    db.commit()
    db.refresh(msg)
    _invalidate_subgroup_cache(subgroup_id)
    try:
        newly_achieved = record_subgroup_message_milestone(
            db,
            user.id,
            username=user.username,
            subgroup_id=subgroup_id,
            message_id=msg.id,
        )
    except Exception:
        logger.exception(
            "Failed to record subgroup message milestone for user %s",
            user.id,
        )
        newly_achieved = []
    return SubgroupMessageOut(
        id=msg.id,
        user_id=msg.user_id,
        username=user.username,
        body=msg.body,
        created_at=msg.created_at,
        newly_achieved=newly_achieved,
    )


@router.delete(
    "/{subgroup_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_message(
    subgroup_id: int,
    message_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = _get_member(db, subgroup_id, user.id)
    if not m or m.role != "admin":
        raise HTTPException(status_code=403, detail="Only subgroup admins can delete messages")

    msg = (
        db.query(SubgroupMessage)
        .filter(
            SubgroupMessage.id == message_id,
            SubgroupMessage.subgroup_id == subgroup_id,
        )
        .first()
    )
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(msg)
    db.commit()
    return None
