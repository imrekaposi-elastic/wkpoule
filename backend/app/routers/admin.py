from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_admin_user
from app.database import get_db
from app.models.prediction import Prediction
from app.models.subgroup import Subgroup, SubgroupMember
from app.models.user import User
from app.schemas.admin import (
    AdminSubgroupMemberOut,
    AdminSubgroupOut,
    AdminUserOut,
    AdminUserRoleIn,
)

router = APIRouter()


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    _admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.id).all()


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user_role(
    user_id: int,
    body: AdminUserRoleIn,
    _admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    if body.is_admin == target.is_admin:
        return target

    if target.is_admin and not body.is_admin:
        n_admins = db.query(User).filter(User.is_admin.is_(True)).count()
        if n_admins < 2:
            raise HTTPException(
                status_code=400,
                detail="Cannot demote the only administrator",
            )

    target.is_admin = body.is_admin
    db.commit()
    db.refresh(target)
    return target


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    if target.is_admin:
        n_admins = db.query(User).filter(User.is_admin.is_(True)).count()
        if n_admins < 2:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the only administrator",
            )

    db.query(Prediction).filter(Prediction.user_id == user_id).delete(
        synchronize_session=False
    )
    db.delete(target)
    db.commit()
    return None


@router.get("/subgroups", response_model=list[AdminSubgroupOut])
def list_all_subgroups(
    _admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    subgroups = db.query(Subgroup).order_by(Subgroup.id).all()
    out: list[AdminSubgroupOut] = []
    for sg in subgroups:
        rows = (
            db.query(SubgroupMember.user_id, User.username, SubgroupMember.role)
            .join(User, User.id == SubgroupMember.user_id)
            .filter(SubgroupMember.subgroup_id == sg.id)
            .order_by(SubgroupMember.role.desc(), User.username)
            .all()
        )
        members = [
            AdminSubgroupMemberOut(user_id=uid, username=uname, role=role)
            for uid, uname, role in rows
        ]
        out.append(
            AdminSubgroupOut(
                id=sg.id,
                name=sg.name,
                created_at=sg.created_at,
                member_count=len(members),
                members=members,
            )
        )
    return out


@router.delete("/subgroups/{subgroup_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_empty_subgroup(
    subgroup_id: int,
    _admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    cnt = (
        db.query(func.count())
        .select_from(SubgroupMember)
        .filter(SubgroupMember.subgroup_id == subgroup_id)
        .scalar()
    )
    if int(cnt or 0) > 0:
        raise HTTPException(
            status_code=400,
            detail="Subgroup still has members; only empty subgroups can be deleted here",
        )
    sg = db.query(Subgroup).filter(Subgroup.id == subgroup_id).first()
    if sg is None:
        raise HTTPException(status_code=404, detail="Subgroup not found")
    db.delete(sg)
    db.commit()
    return None
