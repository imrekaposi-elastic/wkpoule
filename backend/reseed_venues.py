"""Refresh venue review/accessibility Spanish and Italian texts from seed_data.VENUES."""

from app.database import SessionLocal
from app.models.venue import Venue
from seed_data import VENUES


def main() -> None:
    db = SessionLocal()
    try:
        updated = 0
        for v in VENUES:
            row = db.query(Venue).filter(Venue.name == v["name"]).first()
            if not row:
                continue
            row.review_es = v.get("review_es")
            row.review_it = v.get("review_it")
            row.accessibility_es = v.get("accessibility_es")
            row.accessibility_it = v.get("accessibility_it")
            updated += 1
        db.commit()
        print(f"Updated {updated} venues with ES/IT review and accessibility texts.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
