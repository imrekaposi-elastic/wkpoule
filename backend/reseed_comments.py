"""Re-generate all fun comments using unique per-match comments."""

import random

from app.database import SessionLocal
from app.models.fun_comment import FunComment
from app.models.match import Match
from app.models.team import Team
from app.models.venue import Venue
from fun_comment_locales import locales_for_comment_bundle
from match_comments import (
    MATCH_COMMENTS,
    KNOCKOUT_MATCH_COMMENTS,
    KNOCKOUT_TEMPLATES,
    ALL_STYLE_NAMES,
)

import app.models  # noqa: F401


def reseed_comments():
    db = SessionLocal()
    try:
        db.query(FunComment).delete()

        teams = {t.id: t for t in db.query(Team).all()}
        venues = {v.id: v for v in db.query(Venue).all()}
        matches = db.query(Match).order_by(Match.match_number).all()

        random.seed(2026)
        count = 0

        for m in matches:
            mn = m.match_number
            venue = venues.get(m.venue_id)

            if mn in MATCH_COMMENTS:
                c = MATCH_COMMENTS[mn]
                text_it, text_es = locales_for_comment_bundle(c)
                db.add(FunComment(
                    match_id=m.id,
                    comment_text=c["en"],
                    comment_text_nl=c["nl"],
                    comment_text_pt=c["pt"],
                    comment_text_de=c["de"],
                    comment_text_it=text_it,
                    comment_text_es=text_es,
                    style=c["style"],
                ))
                count += 1
            elif mn in KNOCKOUT_MATCH_COMMENTS:
                c = KNOCKOUT_MATCH_COMMENTS[mn]
                text_it, text_es = locales_for_comment_bundle(c)
                db.add(FunComment(
                    match_id=m.id,
                    comment_text=c["en"],
                    comment_text_nl=c["nl"],
                    comment_text_pt=c["pt"],
                    comment_text_de=c["de"],
                    comment_text_it=text_it,
                    comment_text_es=text_es,
                    style=c["style"],
                ))
                count += 1
            elif m.home_team_id is None:
                style = random.choice(ALL_STYLE_NAMES)
                tmpl = KNOCKOUT_TEMPLATES.get(style, KNOCKOUT_TEMPLATES["lineker"])
                text_it, text_es = locales_for_comment_bundle(tmpl)
                db.add(FunComment(
                    match_id=m.id,
                    comment_text=tmpl["en"],
                    comment_text_nl=tmpl["nl"],
                    comment_text_pt=tmpl["pt"],
                    comment_text_de=tmpl["de"],
                    comment_text_it=text_it,
                    comment_text_es=text_es,
                    style=style,
                ))
                count += 1

        db.commit()
        print(f"Re-seeded {count} fun comments (6 languages each).")
        ko_custom = sum(
            1 for x in matches if x.match_number in KNOCKOUT_MATCH_COMMENTS
        )
        ko_template = count - len(MATCH_COMMENTS) - ko_custom
        print(f"  - {len(MATCH_COMMENTS)} unique group-stage comments")
        print(f"  - {ko_custom} unique knockout comments (venues & history)")
        print(f"  - {ko_template} knockout template comments (fallback)")
        style_counts = {}
        for c in db.query(FunComment).all():
            style_counts[c.style] = style_counts.get(c.style, 0) + 1
        for s, n in sorted(style_counts.items()):
            print(f"  {s}: {n} comments")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reseed_comments()
