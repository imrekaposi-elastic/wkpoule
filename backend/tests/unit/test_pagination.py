"""Pagination helpers and list endpoints."""

from app.schemas.pagination import paginate_list
from app.services.subgroup_rankings import compute_participant_rankings
from app.models.user import User


def test_paginate_list_returns_page_slice():
    items = list(range(1, 46))
    page = paginate_list(items, page=2, page_size=20)
    assert page.items == list(range(21, 41))
    assert page.total == 45
    assert page.page == 2
    assert page.page_size == 20
    assert page.total_pages == 3


def test_paginate_list_caps_page_size_at_20():
    items = list(range(30))
    page = paginate_list(items, page=1, page_size=100)
    assert len(page.items) == 20
    assert page.page_size == 20


def test_rankings_endpoint_pagination_via_service(db):
    for i in range(25):
        db.add(
            User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password_hash="x",
                is_admin=False,
            )
        )
    db.commit()
    all_rows = compute_participant_rankings(db, None)
    page1 = paginate_list(all_rows, 1, 20)
    page2 = paginate_list(all_rows, 2, 20)
    assert len(page1.items) == 20
    assert len(page2.items) == 5
    assert page1.total == 25
