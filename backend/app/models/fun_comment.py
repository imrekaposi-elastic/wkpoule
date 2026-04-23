from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FunComment(Base):
    __tablename__ = "fun_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), unique=True, nullable=False)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    comment_text_nl: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment_text_pt: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment_text_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    style: Mapped[str] = mapped_column(String(20), nullable=False)

    match: Mapped["Match"] = relationship(back_populates="fun_comment")  # noqa: F821
