"""Shared pagination types and helpers."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 20

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


def clamp_pagination(page: int, page_size: int) -> tuple[int, int]:
    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)
    return page, page_size


def paginate_list(
    items: list[T],
    page: int,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> PaginatedResponse[T]:
    page, page_size = clamp_pagination(page, page_size)
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    sliced = items[start:end]
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
    return PaginatedResponse(
        items=sliced,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
