from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    stage: Mapped[str] = mapped_column(String(20), nullable=False)
    group_letter: Mapped[str | None] = mapped_column(String(1), nullable=True)
    home_team_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teams.id"), nullable=True)
    away_team_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teams.id"), nullable=True)
    venue_id: Mapped[int] = mapped_column(Integer, ForeignKey("venues.id"), nullable=False)
    kickoff_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="upcoming")

    home_team: Mapped["Team"] = relationship(foreign_keys=[home_team_id])  # noqa: F821
    away_team: Mapped["Team"] = relationship(foreign_keys=[away_team_id])  # noqa: F821
    venue: Mapped["Venue"] = relationship()  # noqa: F821
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="match")  # noqa: F821
    fun_comment: Mapped["FunComment | None"] = relationship(back_populates="match", uselist=False)  # noqa: F821
