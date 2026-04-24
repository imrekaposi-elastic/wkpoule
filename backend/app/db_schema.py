"""Lightweight schema patches for existing DBs (create_all does not add new columns)."""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import get_settings
from app.database import SessionLocal, engine
from app.models.user import User

logger = logging.getLogger(__name__)


def _backfill_venue_hebrew(conn) -> None:
    """Fill review_he / accessibility_he from seed_data when columns were added to an existing DB."""
    try:
        from seed_data import VENUES
    except ImportError:
        logger.debug("seed_data not importable; skipping venue Hebrew backfill")
        return
    for v in VENUES:
        rh = v.get("review_he")
        ah = v.get("accessibility_he")
        if not rh or not ah:
            continue
        conn.execute(
            text(
                "UPDATE venues SET review_he = :rh, accessibility_he = :ah "
                "WHERE name = :n AND review_he IS NULL"
            ),
            {"rh": rh, "ah": ah, "n": v["name"]},
        )


def ensure_schema() -> None:
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "postgresql":
            conn.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10) NOT NULL DEFAULT 'en'"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE subgroup_members "
                    "ADD COLUMN IF NOT EXISTS last_read_message_id INTEGER"
                )
            )
            conn.execute(
                text("ALTER TABLE venues ADD COLUMN IF NOT EXISTS review_he TEXT")
            )
            conn.execute(
                text(
                    "ALTER TABLE venues ADD COLUMN IF NOT EXISTS accessibility_he TEXT"
                )
            )
        elif dialect == "sqlite":
            insp = inspect(engine)
            user_cols = {c["name"] for c in insp.get_columns("users")}
            if "preferred_language" not in user_cols:
                conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN preferred_language VARCHAR(10) NOT NULL DEFAULT 'en'"
                    )
                )
            cols = {c["name"] for c in insp.get_columns("subgroup_members")}
            if "last_read_message_id" not in cols:
                conn.execute(
                    text(
                        "ALTER TABLE subgroup_members "
                        "ADD COLUMN last_read_message_id INTEGER"
                    )
                )
            vcols = {c["name"] for c in insp.get_columns("venues")}
            if "review_he" not in vcols:
                conn.execute(text("ALTER TABLE venues ADD COLUMN review_he TEXT"))
            if "accessibility_he" not in vcols:
                conn.execute(
                    text("ALTER TABLE venues ADD COLUMN accessibility_he TEXT")
                )

        _backfill_venue_hebrew(conn)

        conn.execute(
            text(
                """
                UPDATE subgroup_members
                SET last_read_message_id = (
                    SELECT MAX(id) FROM subgroup_messages m
                    WHERE m.subgroup_id = subgroup_members.subgroup_id
                )
                WHERE last_read_message_id IS NULL
                AND EXISTS (
                    SELECT 1 FROM subgroup_messages m2
                    WHERE m2.subgroup_id = subgroup_members.subgroup_id
                )
                """
            )
        )


def ensure_admin_account(db: Session) -> None:
    """If no administrator exists, promote or create ``admin`` (seed skips when data already exists)."""
    n_admins = db.query(User).filter(User.is_admin.is_(True)).count()
    if n_admins > 0:
        return
    row = db.query(User).filter(User.username == "admin").first()
    if row:
        row.is_admin = True
        db.commit()
        logger.warning(
            "No administrator was configured; promoted existing user 'admin' to administrator."
        )
        return
    db.add(
        User(
            username="admin",
            email="admin@wkpoule.com",
            password_hash=hash_password("admin123"),
            is_admin=True,
        )
    )
    db.commit()
    logger.warning(
        "No administrator was configured; created default user admin / admin123 — change the password after login."
    )


def apply_bootstrap_admin_password(db: Session) -> None:
    """When WKPOULE_BOOTSTRAP_ADMIN_PASSWORD is set, force-reset the ``admin`` login (local/dev recovery)."""
    pwd = (get_settings().bootstrap_admin_password or "").strip()
    if not pwd:
        return
    row = db.query(User).filter(User.username == "admin").first()
    if row is None:
        db.add(
            User(
                username="admin",
                email="admin@wkpoule.com",
                password_hash=hash_password(pwd),
                is_admin=True,
            )
        )
    else:
        row.password_hash = hash_password(pwd)
        row.is_admin = True
    db.commit()
    logger.warning("WKPOULE_BOOTSTRAP_ADMIN_PASSWORD applied: admin password was reset at startup.")


def ensure_admin_access() -> None:
    """Run after migrations: guarantee an admin exists; optional env-based password reset."""
    db = SessionLocal()
    try:
        ensure_admin_account(db)
        apply_bootstrap_admin_password(db)
    finally:
        db.close()
