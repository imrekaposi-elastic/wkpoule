"""Resolve knockout teams from group predictions + Annex C third routing + knockout score predictions.

Round of 32 third-place matchups follow FIFA 2026 Annex C (495 combinations, loaded from data file).
Slot labels follow FIFA notation: 1st = winner (e.g. E1), 2nd = runner-up (e.g. A2), 3rd (e.g. F3).

Knockout draws on tied predicted scores: lower world_ranking wins (better FIFA rank).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.team import Team
from app.schemas.match import TeamOut
from app.services.annex_c import annex_lookup
from app.schemas.ranking import GroupTable
from app.services.prediction_advance import predicted_winner_team_id
from app.services.virtual_standings import best_third_place_team_ids, compute_virtual_group_standings

R16_SOURCES: dict[int, tuple[int, int]] = {
    89: (74, 77),
    90: (73, 75),
    91: (76, 78),
    92: (79, 80),
    93: (83, 84),
    94: (81, 82),
    95: (86, 88),
    96: (85, 87),
}

QF_SOURCES: dict[int, tuple[int, int]] = {
    97: (89, 90),
    98: (93, 94),
    99: (91, 92),
    100: (95, 96),
}

SF_SOURCES: dict[int, tuple[int, int]] = {
    101: (97, 98),
    102: (99, 100),
}

FINAL_SOURCES: dict[int, tuple[int, int]] = {104: (101, 102)}

# R32: (home_position, away_position) where each is ("2","A") runner-up A, ("1","F") winner F,
# or ("3", annex_winner_key) meaning third that faces winner of that letter per Annex row.
R32_STRUCTURE: dict[int, tuple[tuple[str, str], tuple[str, str]]] = {
    73: (("2", "A"), ("2", "B")),
    74: (("1", "E"), ("3", "E")),
    75: (("1", "F"), ("2", "C")),
    76: (("1", "C"), ("2", "F")),
    77: (("1", "I"), ("3", "I")),
    78: (("2", "E"), ("2", "I")),
    79: (("1", "A"), ("3", "A")),
    80: (("1", "L"), ("3", "L")),
    81: (("1", "D"), ("3", "D")),
    82: (("1", "G"), ("3", "G")),
    83: (("2", "K"), ("2", "L")),
    84: (("1", "H"), ("2", "J")),
    85: (("1", "B"), ("3", "B")),
    86: (("1", "J"), ("2", "H")),
    87: (("1", "K"), ("3", "K")),
    88: (("2", "D"), ("2", "G")),
}


def _winner_from_scores(
    home_id: int,
    away_id: int,
    home_score: int,
    away_score: int,
    teams_by_id: dict[int, Team],
) -> int:
    if home_score > away_score:
        return home_id
    if home_score < away_score:
        return away_id
    th, ta = teams_by_id[home_id], teams_by_id[away_id]
    return home_id if th.world_ranking <= ta.world_ranking else away_id


def _first(gt_by: dict[str, GroupTable], letter: str) -> int | None:
    g = gt_by.get(letter.upper())
    if not g or len(g.standings) < 1:
        return None
    return g.standings[0].team_id


def _second(gt_by: dict[str, GroupTable], letter: str) -> int | None:
    g = gt_by.get(letter.upper())
    if not g or len(g.standings) < 2:
        return None
    return g.standings[1].team_id


def _third_in_group(gt_by: dict[str, GroupTable], letter: str) -> int | None:
    g = gt_by.get(letter.upper())
    if not g or len(g.standings) < 3:
        return None
    return g.standings[2].team_id


def _slot_label(kind: str, letter: str) -> str:
    kind = kind.strip()
    letter = letter.upper()
    if kind == "1":
        return f"{letter}1"
    if kind == "2":
        return f"{letter}2"
    if kind == "3":
        return f"{letter}3"
    return f"{letter}{kind}"


def _groups_with_advancing_thirds(tables: list[GroupTable], best_third_ids: set[int]) -> frozenset[str]:
    letters: list[str] = []
    for gt in tables:
        if len(gt.standings) < 3:
            continue
        third_id = gt.standings[2].team_id
        if third_id in best_third_ids:
            letters.append(gt.group_letter.upper())
    return frozenset(letters)


def build_r32_from_annex(
    gt_by: dict[str, GroupTable],
    annex_third_for_winner: dict[str, str],
) -> tuple[dict[int, tuple[int | None, int | None]], dict[int, tuple[str | None, str | None]]]:
    """Resolve R32 team ids and FIFA slot labels."""
    pairs: dict[int, tuple[int | None, int | None]] = {}
    labels: dict[int, tuple[str | None, str | None]] = {}

    def resolve_side(spec: tuple[str, str]) -> tuple[int | None, str | None]:
        kind, letter = spec
        if kind == "1":
            return _first(gt_by, letter), _slot_label("1", letter)
        if kind == "2":
            return _second(gt_by, letter), _slot_label("2", letter)
        if kind == "3":
            # Third that faces winner `letter`: Annex maps winner letter -> third's group letter
            third_group = annex_third_for_winner.get(letter.upper())
            if not third_group:
                return None, None
            tid = _third_in_group(gt_by, third_group)
            return tid, _slot_label("3", third_group)
        return None, None

    for mn, (home_spec, away_spec) in R32_STRUCTURE.items():
        ht, hl = resolve_side(home_spec)
        at, al = resolve_side(away_spec)
        pairs[mn] = (ht, at)
        labels[mn] = (hl, al)

    return pairs, labels


def compute_predicted_knockout_teams(
    db: Session, user_id: int
) -> tuple[
    dict[int, tuple[TeamOut | None, TeamOut | None]],
    dict[int, tuple[str | None, str | None]],
]:
    """Predicted TeamOut pairs and FIFA slot labels for matches 73–104."""
    teams_by_id = {t.id: t for t in db.query(Team).all()}
    tables = compute_virtual_group_standings(db, user_id)
    gt_by = {gt.group_letter.upper(): gt for gt in tables}

    best_ids = best_third_place_team_ids(tables)
    advancing = _groups_with_advancing_thirds(tables, best_ids)

    annex_table = annex_lookup()
    annex_row = annex_table.get(advancing)
    if annex_row is None or len(advancing) != 8:
        annex_row = {}

    r32_pairs: dict[int, tuple[int | None, int | None]]
    r32_labels: dict[int, tuple[str | None, str | None]]
    if annex_row:
        r32_pairs, r32_labels = build_r32_from_annex(gt_by, annex_row)
    else:
        r32_pairs = {mn: (None, None) for mn in range(73, 89)}
        r32_labels = {mn: (None, None) for mn in range(73, 89)}

    matches = (
        db.query(Match).filter(Match.match_number >= 73, Match.match_number <= 104).order_by(Match.match_number).all()
    )
    by_num = {m.match_number: m for m in matches}
    preds = db.query(Prediction).filter(Prediction.user_id == user_id).all()
    pred_by_mid = {p.match_id: p for p in preds}

    computed: dict[int, tuple[int | None, int | None]] = {}
    winners: dict[int, int | None] = {}
    slot_labels: dict[int, tuple[str | None, str | None]] = dict(r32_labels)

    def win_from_pred(mn: int, home_id: int | None, away_id: int | None) -> int | None:
        if home_id is None or away_id is None:
            return None
        m = by_num.get(mn)
        if not m:
            return None
        p = pred_by_mid.get(m.id)
        if p is None:
            return None
        return predicted_winner_team_id(
            home_id,
            away_id,
            p.home_score,
            p.away_score,
            teams_by_id,
            p.advance_team_id,
        )

    for mn in range(73, 89):
        computed[mn] = r32_pairs.get(mn, (None, None))
        winners[mn] = win_from_pred(mn, computed[mn][0], computed[mn][1])

    for mn in range(89, 97):
        hm, am = R16_SOURCES[mn]
        h, a = winners.get(hm), winners.get(am)
        computed[mn] = (h, a)
        winners[mn] = win_from_pred(mn, h, a)
        slot_labels[mn] = (f"W{hm}", f"W{am}")

    for mn in range(97, 101):
        hm, am = QF_SOURCES[mn]
        h, a = winners.get(hm), winners.get(am)
        computed[mn] = (h, a)
        winners[mn] = win_from_pred(mn, h, a)
        slot_labels[mn] = (f"W{hm}", f"W{am}")

    for mn in range(101, 103):
        hm, am = SF_SOURCES[mn]
        h, a = winners.get(hm), winners.get(am)
        computed[mn] = (h, a)
        winners[mn] = win_from_pred(mn, h, a)
        slot_labels[mn] = (f"W{hm}", f"W{am}")

    def loser_from(mn: int) -> int | None:
        hid, aid = computed[mn]
        if hid is None or aid is None:
            return None
        m = by_num.get(mn)
        if not m:
            return None
        p = pred_by_mid.get(m.id)
        if p is None:
            return None
        w = predicted_winner_team_id(
            hid, aid, p.home_score, p.away_score, teams_by_id, p.advance_team_id
        )
        return aid if w == hid else hid

    computed[103] = (loser_from(101), loser_from(102))
    slot_labels[103] = ("L101", "L102")

    hm, am = FINAL_SOURCES[104]
    computed[104] = (winners.get(hm), winners.get(am))
    slot_labels[104] = (f"W{hm}", f"W{am}")

    out_teams: dict[int, tuple[TeamOut | None, TeamOut | None]] = {}

    def out_pair(hid: int | None, aid: int | None) -> tuple[TeamOut | None, TeamOut | None]:
        ho = TeamOut.model_validate(teams_by_id[hid]) if hid is not None and hid in teams_by_id else None
        ao = TeamOut.model_validate(teams_by_id[aid]) if aid is not None and aid in teams_by_id else None
        return ho, ao

    for mn in range(73, 105):
        if mn in computed:
            out_teams[mn] = out_pair(*computed[mn])

    return out_teams, slot_labels
