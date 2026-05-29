"""Subgroup membership application flow."""

from app.models.subgroup import Subgroup, SubgroupJoinRequest, SubgroupMember
from app.models.user import User
from app.services.subgroup_join_requests import (
    approve_join_request,
    membership_status_for_user,
    pending_request_for_user,
)


def test_apply_and_approve_join_request(db):
    admin = User(
        username="admin_sg",
        email="admin_sg@example.com",
        password_hash="x",
    )
    applicant = User(
        username="applicant",
        email="applicant@example.com",
        password_hash="x",
    )
    db.add_all([admin, applicant])
    db.flush()
    sg = Subgroup(name="Elastic", created_by_user_id=admin.id)
    db.add(sg)
    db.flush()
    db.add(SubgroupMember(subgroup_id=sg.id, user_id=admin.id, role="admin"))
    db.commit()

    assert membership_status_for_user(db, sg.id, applicant.id) == "none"

    req = SubgroupJoinRequest(subgroup_id=sg.id, user_id=applicant.id, status="pending")
    db.add(req)
    db.commit()

    assert membership_status_for_user(db, sg.id, applicant.id) == "application_pending"
    assert pending_request_for_user(db, sg.id, applicant.id) is not None

    approve_join_request(db, req, admin.id)
    db.commit()

    assert membership_status_for_user(db, sg.id, applicant.id) == "member"
    member = (
        db.query(SubgroupMember)
        .filter(
            SubgroupMember.subgroup_id == sg.id,
            SubgroupMember.user_id == applicant.id,
        )
        .first()
    )
    assert member is not None
    assert req.status == "approved"
