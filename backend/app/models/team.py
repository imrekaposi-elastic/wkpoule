from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    fifa_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    group_letter: Mapped[str] = mapped_column(String(1), nullable=False)
    world_ranking: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    flag_url: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    qualification_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualification_nl: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualification_pt: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualification_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualification_es: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualification_it: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualification_he: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths_nl: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths_pt: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths_es: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths_it: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths_he: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses_nl: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses_pt: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses_es: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses_it: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses_he: Mapped[str | None] = mapped_column(Text, nullable=True)

    players = relationship(
        "TeamPlayer",
        back_populates="team",
        cascade="all, delete-orphan",
        order_by="TeamPlayer.sort_order",
    )
