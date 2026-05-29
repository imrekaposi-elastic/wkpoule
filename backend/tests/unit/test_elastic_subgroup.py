"""@elastic.co registration auto-joins the Elastic subgroup."""

from app.models.subgroup import Subgroup, SubgroupMember
from app.models.user import User
from app.services.elastic_subgroup import (
    ELASTIC_SUBGROUP_NAME,
    add_user_to_elastic_subgroup,
    is_elastic_email,
)


def test_is_elastic_email():
    assert is_elastic_email("dev@elastic.co")
    assert is_elastic_email("Dev@Elastic.CO")
    assert not is_elastic_email("dev@elastic.com")
    assert not is_elastic_email("dev@example.com")


def test_add_user_creates_subgroup_and_membership(db):
    user = User(
        username="imre",
        email="imre@elastic.co",
        password_hash="x",
        is_admin=False,
    )
    db.add(user)
    db.flush()

    add_user_to_elastic_subgroup(db, user)
    db.commit()

    sg = db.query(Subgroup).filter(Subgroup.name == ELASTIC_SUBGROUP_NAME).one()
    member = (
        db.query(SubgroupMember)
        .filter(
            SubgroupMember.subgroup_id == sg.id,
            SubgroupMember.user_id == user.id,
        )
        .one()
    )
    assert member.role == "member"


def test_add_user_joins_existing_elastic_subgroup(db):
    owner = User(
        username="owner",
        email="owner@example.com",
        password_hash="x",
        is_admin=True,
    )
    db.add(owner)
    db.flush()
    sg = Subgroup(name=ELASTIC_SUBGROUP_NAME, created_by_user_id=owner.id)
    db.add(sg)
    db.flush()

    user = User(
        username="newhire",
        email="newhire@elastic.co",
        password_hash="x",
        is_admin=False,
    )
    db.add(user)
    db.flush()
    add_user_to_elastic_subgroup(db, user)
    db.commit()

    assert db.query(Subgroup).count() == 1
    assert (
        db.query(SubgroupMember)
        .filter(
            SubgroupMember.subgroup_id == sg.id,
            SubgroupMember.user_id == user.id,
        )
        .count()
        == 1
    )
