"""Lightweight schema patches for existing DBs (create_all does not add new columns)."""

from sqlalchemy import inspect, text

from app.database import engine


def ensure_schema() -> None:
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "postgresql":
            conn.execute(
                text(
                    "ALTER TABLE subgroup_members "
                    "ADD COLUMN IF NOT EXISTS last_read_message_id INTEGER"
                )
            )
        elif dialect == "sqlite":
            insp = inspect(engine)
            cols = {c["name"] for c in insp.get_columns("subgroup_members")}
            if "last_read_message_id" not in cols:
                conn.execute(
                    text(
                        "ALTER TABLE subgroup_members "
                        "ADD COLUMN last_read_message_id INTEGER"
                    )
                )

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
