from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TeamPlayer(Base):
    __tablename__ = "team_players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    position: Mapped[str] = mapped_column(String(10), nullable=False)
    shirt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    club: Mapped[str] = mapped_column(String(160), nullable=False)
    height_cm: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weight_kg: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    caps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    date_of_birth: Mapped[str | None] = mapped_column(String(10), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    team = relationship("Team", back_populates="players")
