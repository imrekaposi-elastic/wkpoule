"""Compare seed_data kickoffs to football-data.org (requires FOOTBALL_DATA_API_KEY)."""

from __future__ import annotations

import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seed_data import GROUP_MATCHES, KNOCKOUT_MATCHES


def main() -> int:
    key = os.environ.get("FOOTBALL_DATA_API_KEY", "")
    if not key:
        print("FOOTBALL_DATA_API_KEY not set", file=sys.stderr)
        return 1

    resp = httpx.get(
        "https://api.football-data.org/v4/competitions/WC/matches",
        headers={"X-Auth-Token": key},
        timeout=60,
    )
    resp.raise_for_status()

    by_pair: dict[tuple[str, str], str] = {}
    knockout_utc: list[str] = []
    for m in resp.json()["matches"]:
        utc = m["utcDate"][:19]
        if m.get("stage") == "GROUP_STAGE":
            ht = m["homeTeam"]["tla"]
            at = m["awayTeam"]["tla"]
            by_pair[(ht, at)] = utc
        else:
            knockout_utc.append(utc)
    knockout_utc.sort()

    mismatches = 0
    for spec in GROUP_MATCHES:
        pair = (spec["home"], spec["away"])
        api_utc = by_pair.get(pair)
        if api_utc is None:
            print(f"mn{spec['mn']:>3} {pair[0]} vs {pair[1]}: missing from API")
            mismatches += 1
            continue
        seed_utc = spec["ko"].strftime("%Y-%m-%dT%H:%M:%S")
        if seed_utc != api_utc:
            print(f"mn{spec['mn']:>3} {pair[0]} vs {pair[1]}: seed={seed_utc} api={api_utc}")
            mismatches += 1

    ko_specs = sorted(KNOCKOUT_MATCHES, key=lambda s: s["mn"])
    if len(ko_specs) != len(knockout_utc):
        print(f"Knockout count mismatch: seed={len(ko_specs)} api={len(knockout_utc)}")
        mismatches += 1
    else:
        for spec, api_utc in zip(ko_specs, knockout_utc):
            seed_utc = spec["ko"].strftime("%Y-%m-%dT%H:%M:%S")
            if seed_utc != api_utc:
                print(f"mn{spec['mn']:>3} knockout: seed={seed_utc} api={api_utc}")
                mismatches += 1

    if mismatches:
        print(f"\n{mismatches} mismatch(es)")
        return 1
    print("All 104 fixtures match football-data.org kickoff times.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
