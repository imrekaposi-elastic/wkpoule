"""Lightweight schema patches for existing DBs (create_all does not add new columns)."""

import logging

from sqlalchemy import bindparam, inspect, text
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import get_settings
from app.database import SessionLocal, engine
from app.models.user import User

logger = logging.getLogger(__name__)


def _ensure_team_player_physical_columns(conn, dialect: str, player_cols: set[str] | None = None) -> None:
    """Add height/weight/DOB columns used by squad backfill (prod may predate the model)."""
    if dialect == "postgresql":
        conn.execute(
            text(
                "ALTER TABLE team_players "
                "ADD COLUMN IF NOT EXISTS height_cm INTEGER NOT NULL DEFAULT 0"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE team_players "
                "ADD COLUMN IF NOT EXISTS weight_kg INTEGER NOT NULL DEFAULT 0"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE team_players "
                "ADD COLUMN IF NOT EXISTS date_of_birth VARCHAR(10)"
            )
        )
        conn.execute(
            text("ALTER TABLE team_players ADD COLUMN IF NOT EXISTS age INTEGER")
        )
        return

    if dialect == "sqlite" and player_cols is not None:
        if "height_cm" not in player_cols:
            conn.execute(
                text(
                    "ALTER TABLE team_players "
                    "ADD COLUMN height_cm INTEGER NOT NULL DEFAULT 0"
                )
            )
        if "weight_kg" not in player_cols:
            conn.execute(
                text(
                    "ALTER TABLE team_players "
                    "ADD COLUMN weight_kg INTEGER NOT NULL DEFAULT 0"
                )
            )
        if "date_of_birth" not in player_cols:
            conn.execute(
                text("ALTER TABLE team_players ADD COLUMN date_of_birth VARCHAR(10)")
            )
        if "age" not in player_cols:
            conn.execute(text("ALTER TABLE team_players ADD COLUMN age INTEGER"))


def _backfill_fun_comment_it_es(conn) -> None:
    """Fill Italian/Spanish from native match_comments data when DB rows predate es/it columns."""
    try:
        from match_comments import (
            KNOCKOUT_MATCH_COMMENTS,
            KNOCKOUT_TEMPLATES,
            MATCH_COMMENTS,
        )
        from fun_comment_locales import locales_for_comment_bundle
    except ImportError:
        logger.debug("match_comments locales not importable; skipping IT/ES backfill")
        return

    try:
        rows = conn.execute(
            text(
                "SELECT id, match_id, comment_text_it, comment_text_es, style "
                "FROM fun_comments"
            )
        ).fetchall()
    except Exception:
        return

    match_ids = {r[1]: r[0] for r in rows}
    match_numbers = {}
    if match_ids:
        mn_rows = conn.execute(
            text("SELECT id, match_number FROM matches WHERE id IN :ids").bindparams(
                bindparam("ids", expanding=True)
            ),
            {"ids": list(match_ids.keys())},
        ).fetchall()
        match_numbers = {mid: mn for mid, mn in mn_rows}

    for rid, match_id, it_val, es_val, style in rows:
        mn = match_numbers.get(match_id)
        if mn is None:
            continue
        bundle = None
        if mn in MATCH_COMMENTS:
            bundle = MATCH_COMMENTS[mn]
        elif mn in KNOCKOUT_MATCH_COMMENTS:
            bundle = KNOCKOUT_MATCH_COMMENTS[mn]
        elif style and style in KNOCKOUT_TEMPLATES:
            bundle = KNOCKOUT_TEMPLATES[style]
        if not bundle:
            continue
        it_new, es_new = locales_for_comment_bundle(bundle)
        if it_val == it_new and es_val == es_new:
            continue
        conn.execute(
            text(
                "UPDATE fun_comments SET comment_text_it = :it, comment_text_es = :es "
                "WHERE id = :id"
            ),
            {"it": it_new, "es": es_new, "id": rid},
        )


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


def _backfill_venue_es_it(conn) -> None:
    """Fill review_es/it and accessibility_es/it from seed_data for existing databases."""
    try:
        from seed_data import VENUES
    except ImportError:
        logger.debug("seed_data not importable; skipping venue ES/IT backfill")
        return
    for v in VENUES:
        res = v.get("review_es")
        rit = v.get("review_it")
        aes = v.get("accessibility_es")
        ait = v.get("accessibility_it")
        if not res or not rit or not aes or not ait:
            continue
        conn.execute(
            text(
                "UPDATE venues SET review_es = :res, review_it = :rit, "
                "accessibility_es = :aes, accessibility_it = :ait "
                "WHERE name = :n AND (review_es IS NULL OR review_es = '')"
            ),
            {"res": res, "rit": rit, "aes": aes, "ait": ait, "n": v["name"]},
        )


def _normalize_user_usernames(conn) -> None:
    """Store usernames in lowercase; resolve case-only duplicates by keeping the oldest account."""
    rows = conn.execute(text("SELECT id, username FROM users ORDER BY id")).fetchall()
    by_lower: dict[str, list[tuple[int, str]]] = {}
    for uid, uname in rows:
        key = (uname or "").strip().lower()
        by_lower.setdefault(key, []).append((uid, uname))

    for key, group in by_lower.items():
        group.sort(key=lambda item: item[0])
        keep_id, keep_name = group[0]
        if keep_name != key:
            conn.execute(
                text("UPDATE users SET username = :username WHERE id = :id"),
                {"username": key, "id": keep_id},
            )
        for uid, uname in group[1:]:
            renamed = f"{key}_{uid}"
            logger.warning(
                "Renaming duplicate username id=%s from %r to %r (kept id=%s as %r)",
                uid,
                uname,
                renamed,
                keep_id,
                key,
            )
            conn.execute(
                text("UPDATE users SET username = :username WHERE id = :id"),
                {"username": renamed, "id": uid},
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
                    "ALTER TABLE users "
                    "ADD COLUMN IF NOT EXISTS include_in_rankings BOOLEAN NOT NULL DEFAULT TRUE"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE subgroup_members "
                    "ADD COLUMN IF NOT EXISTS last_read_message_id INTEGER"
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS subgroup_join_requests (
                        id SERIAL PRIMARY KEY,
                        subgroup_id INTEGER NOT NULL REFERENCES subgroups(id) ON DELETE CASCADE,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        decided_at TIMESTAMPTZ,
                        decided_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                        CONSTRAINT uq_subgroup_join_request_user UNIQUE (subgroup_id, user_id)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_subgroup_join_requests_subgroup_id "
                    "ON subgroup_join_requests (subgroup_id)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_subgroup_join_requests_user_id "
                    "ON subgroup_join_requests (user_id)"
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS user_prediction_milestones (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        milestone_key VARCHAR(64) NOT NULL,
                        achieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        CONSTRAINT uq_user_prediction_milestone UNIQUE (user_id, milestone_key)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_user_prediction_milestones_user_id "
                    "ON user_prediction_milestones (user_id)"
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
            conn.execute(
                text("ALTER TABLE venues ADD COLUMN IF NOT EXISTS review_es TEXT")
            )
            conn.execute(
                text("ALTER TABLE venues ADD COLUMN IF NOT EXISTS review_it TEXT")
            )
            conn.execute(
                text(
                    "ALTER TABLE venues ADD COLUMN IF NOT EXISTS accessibility_es TEXT"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE venues ADD COLUMN IF NOT EXISTS accessibility_it TEXT"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE predictions "
                    "ADD COLUMN IF NOT EXISTS advance_team_id INTEGER REFERENCES teams(id)"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE fun_comments "
                    "ADD COLUMN IF NOT EXISTS comment_text_it TEXT"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE fun_comments "
                    "ADD COLUMN IF NOT EXISTS comment_text_es TEXT"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE teams ADD COLUMN IF NOT EXISTS qualification_en TEXT"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE teams ADD COLUMN IF NOT EXISTS qualification_nl TEXT"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE teams ADD COLUMN IF NOT EXISTS strengths_en TEXT"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE teams ADD COLUMN IF NOT EXISTS strengths_nl TEXT"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE teams ADD COLUMN IF NOT EXISTS weaknesses_en TEXT"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE teams ADD COLUMN IF NOT EXISTS weaknesses_nl TEXT"
                )
            )
            for col in (
                "qualification_pt", "qualification_de", "qualification_es",
                "qualification_it", "qualification_he",
                "strengths_pt", "strengths_de", "strengths_es",
                "strengths_it", "strengths_he",
                "weaknesses_pt", "weaknesses_de", "weaknesses_es",
                "weaknesses_it", "weaknesses_he",
                "qualification_data_json",
            ):
                conn.execute(
                    text(f"ALTER TABLE teams ADD COLUMN IF NOT EXISTS {col} TEXT")
                )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS team_players (
                        id SERIAL PRIMARY KEY,
                        team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                        name VARCHAR(120) NOT NULL,
                        position VARCHAR(10) NOT NULL,
                        shirt_number INTEGER NOT NULL,
                        club VARCHAR(160) NOT NULL,
                        height_cm INTEGER NOT NULL DEFAULT 0,
                        weight_kg INTEGER NOT NULL DEFAULT 0,
                        caps INTEGER NOT NULL DEFAULT 0,
                        sort_order INTEGER NOT NULL DEFAULT 0,
                        date_of_birth VARCHAR(10),
                        age INTEGER
                    )
                    """
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_team_players_team_id "
                    "ON team_players (team_id)"
                )
            )
            _ensure_team_player_physical_columns(conn, dialect)
        elif dialect == "sqlite":
            insp = inspect(engine)
            user_cols = {c["name"] for c in insp.get_columns("users")}
            if "preferred_language" not in user_cols:
                conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN preferred_language VARCHAR(10) NOT NULL DEFAULT 'en'"
                    )
                )
            if "include_in_rankings" not in user_cols:
                conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN include_in_rankings BOOLEAN NOT NULL DEFAULT 1"
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
            tables = set(insp.get_table_names())
            if "subgroup_join_requests" not in tables:
                conn.execute(
                    text(
                        """
                        CREATE TABLE subgroup_join_requests (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            subgroup_id INTEGER NOT NULL REFERENCES subgroups(id) ON DELETE CASCADE,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            status VARCHAR(20) NOT NULL DEFAULT 'pending',
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            decided_at DATETIME,
                            decided_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                            CONSTRAINT uq_subgroup_join_request_user UNIQUE (subgroup_id, user_id)
                        )
                        """
                    )
                )
            if "user_prediction_milestones" not in tables:
                conn.execute(
                    text(
                        """
                        CREATE TABLE user_prediction_milestones (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            milestone_key VARCHAR(64) NOT NULL,
                            achieved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT uq_user_prediction_milestone UNIQUE (user_id, milestone_key)
                        )
                        """
                    )
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_user_prediction_milestones_user_id "
                        "ON user_prediction_milestones (user_id)"
                    )
                )
            vcols = {c["name"] for c in insp.get_columns("venues")}
            if "review_he" not in vcols:
                conn.execute(text("ALTER TABLE venues ADD COLUMN review_he TEXT"))
            if "accessibility_he" not in vcols:
                conn.execute(
                    text("ALTER TABLE venues ADD COLUMN accessibility_he TEXT")
                )
            if "review_es" not in vcols:
                conn.execute(text("ALTER TABLE venues ADD COLUMN review_es TEXT"))
            if "review_it" not in vcols:
                conn.execute(text("ALTER TABLE venues ADD COLUMN review_it TEXT"))
            if "accessibility_es" not in vcols:
                conn.execute(
                    text("ALTER TABLE venues ADD COLUMN accessibility_es TEXT")
                )
            if "accessibility_it" not in vcols:
                conn.execute(
                    text("ALTER TABLE venues ADD COLUMN accessibility_it TEXT")
                )
            pred_cols = {c["name"] for c in insp.get_columns("predictions")}
            if "advance_team_id" not in pred_cols:
                conn.execute(
                    text(
                        "ALTER TABLE predictions "
                        "ADD COLUMN advance_team_id INTEGER REFERENCES teams(id)"
                    )
                )
            fc_cols = {c["name"] for c in insp.get_columns("fun_comments")}
            if "comment_text_it" not in fc_cols:
                conn.execute(
                    text("ALTER TABLE fun_comments ADD COLUMN comment_text_it TEXT")
                )
            if "comment_text_es" not in fc_cols:
                conn.execute(
                    text("ALTER TABLE fun_comments ADD COLUMN comment_text_es TEXT")
                )
            team_cols = {c["name"] for c in insp.get_columns("teams")}
            for col in (
                "qualification_en",
                "qualification_nl",
                "qualification_pt",
                "qualification_de",
                "qualification_es",
                "qualification_it",
                "qualification_he",
                "strengths_en",
                "strengths_nl",
                "strengths_pt",
                "strengths_de",
                "strengths_es",
                "strengths_it",
                "strengths_he",
                "weaknesses_en",
                "weaknesses_nl",
                "weaknesses_pt",
                "weaknesses_de",
                "weaknesses_es",
                "weaknesses_it",
                "weaknesses_he",
                "qualification_data_json",
            ):
                if col not in team_cols:
                    conn.execute(text(f"ALTER TABLE teams ADD COLUMN {col} TEXT"))
            if "team_players" not in tables:
                conn.execute(
                    text(
                        """
                        CREATE TABLE team_players (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                            name VARCHAR(120) NOT NULL,
                            position VARCHAR(10) NOT NULL,
                            shirt_number INTEGER NOT NULL,
                            club VARCHAR(160) NOT NULL,
                            height_cm INTEGER NOT NULL DEFAULT 0,
                            weight_kg INTEGER NOT NULL DEFAULT 0,
                            caps INTEGER NOT NULL DEFAULT 0,
                            sort_order INTEGER NOT NULL DEFAULT 0,
                            date_of_birth VARCHAR(10),
                            age INTEGER
                        )
                        """
                    )
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_team_players_team_id "
                        "ON team_players (team_id)"
                    )
                )
            else:
                player_cols = {c["name"] for c in insp.get_columns("team_players")}
                _ensure_team_player_physical_columns(conn, dialect, player_cols)

        _backfill_venue_hebrew(conn)
        _backfill_venue_es_it(conn)
        _backfill_fun_comment_it_es(conn)
        _normalize_user_usernames(conn)

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

    _backfill_team_content()


def _backfill_team_content() -> None:
    """Fill team profiles and illustrative squads on existing databases."""
    try:
        from app.services.team_content import backfill_all_teams
    except ImportError:
        logger.debug("team_content not importable; skipping team backfill")
        return
    db = SessionLocal()
    try:
        backfill_all_teams(db)
    except Exception:
        db.rollback()
        logger.exception("Team profile/squad backfill failed")
    finally:
        db.close()


def ensure_admin_account(db: Session) -> None:
    """If no administrator exists, promote or create ``admin`` (seed skips when data already exists)."""
    n_admins = db.query(User).filter(User.is_admin.is_(True)).count()
    if n_admins > 0:
        return
    row = db.query(User).filter(User.username == "admin").first()
    if row:
        row.is_admin = True
        row.include_in_rankings = False
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
            include_in_rankings=False,
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
                include_in_rankings=False,
            )
        )
    else:
        row.password_hash = hash_password(pwd)
        row.is_admin = True
        row.include_in_rankings = False
    db.commit()
    logger.warning("WKPOULE_BOOTSTRAP_ADMIN_PASSWORD applied: admin password was reset at startup.")


def ensure_admin_access() -> None:
    """Run after migrations: guarantee an admin exists; optional env-based password reset."""
    db = SessionLocal()
    try:
        ensure_admin_account(db)
        apply_bootstrap_admin_password(db)
        from app.services.elastic_subgroup import ensure_elastic_subgroup_admins

        ensure_elastic_subgroup_admins(db)
    finally:
        db.close()
