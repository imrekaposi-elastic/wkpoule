from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserPredictionMilestone(Base):
    """First time a user tipped every match in a tournament phase (see milestone_key)."""

    __tablename__ = "user_prediction_milestones"
    __table_args__ = (
        UniqueConstraint("user_id", "milestone_key", name="uq_user_prediction_milestone"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    milestone_key: Mapped[str] = mapped_column(String(64), nullable=False)
    achieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="prediction_milestones")
