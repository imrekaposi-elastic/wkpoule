from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    fifa_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    group_letter: Mapped[str] = mapped_column(String(1), nullable=False)
    world_ranking: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    flag_url: Mapped[str] = mapped_column(String(255), nullable=False, default="")
