from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Subgroup(Base):
    __tablename__ = "subgroups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    members: Mapped[list["SubgroupMember"]] = relationship(
        back_populates="subgroup",
        cascade="all, delete-orphan",
    )
    invites: Mapped[list["SubgroupInvite"]] = relationship(
        back_populates="subgroup",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["SubgroupMessage"]] = relationship(
        back_populates="subgroup",
        cascade="all, delete-orphan",
    )
    join_requests: Mapped[list["SubgroupJoinRequest"]] = relationship(
        back_populates="subgroup",
        cascade="all, delete-orphan",
    )


class SubgroupJoinRequest(Base):
    """User-initiated request to join a subgroup; subgroup admin approves or rejects."""

    __tablename__ = "subgroup_join_requests"
    __table_args__ = (
        UniqueConstraint("subgroup_id", "user_id", name="uq_subgroup_join_request_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subgroup_id: Mapped[int] = mapped_column(
        ForeignKey("subgroups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    subgroup: Mapped["Subgroup"] = relationship(back_populates="join_requests")


class SubgroupMember(Base):
    __tablename__ = "subgroup_members"
    __table_args__ = (UniqueConstraint("subgroup_id", "user_id", name="uq_subgroup_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subgroup_id: Mapped[int] = mapped_column(
        ForeignKey("subgroups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    # Highest subgroup_messages.id the user has seen in chat; unread = messages from others with id > this.
    last_read_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    subgroup: Mapped["Subgroup"] = relationship(back_populates="members")


class SubgroupInvite(Base):
    __tablename__ = "subgroup_invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subgroup_id: Mapped[int] = mapped_column(
        ForeignKey("subgroups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    invited_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    subgroup: Mapped["Subgroup"] = relationship(back_populates="invites")


class SubgroupMessage(Base):
    __tablename__ = "subgroup_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subgroup_id: Mapped[int] = mapped_column(
        ForeignKey("subgroups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    subgroup: Mapped["Subgroup"] = relationship(back_populates="messages")
