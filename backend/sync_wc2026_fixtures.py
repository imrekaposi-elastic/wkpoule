"""Apply canonical WC 2026 venues and kickoffs from seed_data to an existing database.

Usage (from backend/):
    python sync_wc2026_fixtures.py

Updates match.venue_id and match.kickoff_utc for all 104 fixtures by match_number.
Safe to re-run; does not touch scores, predictions, or comments.
"""

from __future__ import annotations

from seed_data import GROUP_MATCHES, KNOCKOUT_MATCHES

from app.database import SessionLocal
from app.models.match import Match
from app.models.venue import Venue


def main() -> None:
    fixtures = GROUP_MATCHES + KNOCKOUT_MATCHES
    db = SessionLocal()
    try:
        venues = {v.name: v for v in db.query(Venue).all()}
        missing_venues = sorted({f["venue"] for f in fixtures if f["venue"] not in venues})
        if missing_venues:
            raise SystemExit(f"Missing venues in database: {', '.join(missing_venues)}")

        updated = 0
        for spec in fixtures:
            match = db.query(Match).filter(Match.match_number == spec["mn"]).first()
            if match is None:
                print(f"skip match {spec['mn']}: not in database")
                continue
            venue = venues[spec["venue"]]
            if match.venue_id != venue.id or match.kickoff_utc != spec["ko"]:
                match.venue_id = venue.id
                match.kickoff_utc = spec["ko"]
                updated += 1

        db.commit()
        print(f"Synced {updated} match(es) from seed_data fixture list.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
