from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_nl: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_pt: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_temp_celsius: Mapped[float | None] = mapped_column(Float, nullable=True)
    city_attractiveness: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accessibility_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessibility_nl: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessibility_pt: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessibility_de: Mapped[str | None] = mapped_column(Text, nullable=True)
