# WK Poule — Agent context (bugs, fixes, invariants)

Read this before changing knockout scoring, bracket resolution, or football-data.org sync.
For API auth and prediction workflows, use `docs/AGENTS.md`. For OpenAPI, use `/openapi.json`.

**Current app version:** `2.7.4` (`frontend/src/version.ts`, `backend/app/main.py`).

---

## Repo map (relevant to past bugs)

| Area | Path |
|------|------|
| football-data.org score poller | `backend/app/services/score_poller.py` → `score_sync.py` |
| 90-min goal extraction from API | `backend/app/services/match_fixture_sync.py` |
| Knockout bracket / next-round teams | `backend/app/services/bracket_resolver.py` |
| Virtual group tables (played = real, rest = predicted) | `backend/app/services/virtual_standings.py` |
| Tip points / winner resolution | `backend/app/services/scoring.py` |
| Admin score override | `backend/app/routers/matches.py` (`PATCH /{match_id}/score`) |
| Match list with `?predicted_teams=true` | `backend/app/routers/matches.py` → `_match_to_out()` |
| Knockout advance validation | `backend/app/services/prediction_advance.py` |
| Schema migrations (no Alembic) | `backend/app/db_schema.py` |
| Rankings pagination helpers (frontend) | `frontend/src/utils/rankings.ts` |
| Redis cache layer | `backend/app/cache/` |
| Shared global rankings cache | `backend/app/services/rankings_cache.py` |
| OpenShift app manifests (replicas, Redis) | `openshift/base/` |
| Acc env (1 replica API/frontend) | `openshift/overlays/acc/kustomization.yaml` |
| OTel + Redis observability | `openshift/base/otel-collector.yaml`, `openshift/redis-dashboard.json` |
| Full original plan (phased) | `docs/redis-caching-observability-test-coverage-plan.md` |

---

## Performance & scaling plan (stated → implemented)

**Goal:** Handle match-night traffic for a company-sized pool (~50–300 concurrent browsers) without rewriting the app. Strategy: **Redis read-through cache**, **shared hot keys**, **horizontal pod scaling (1 uvicorn worker per pod)**, **observability** — not multi-worker uvicorn or heavy DB pagination (only 104 matches).

**Canonical plan doc:** `docs/redis-caching-observability-test-coverage-plan.md` (created ~Jun 2026). Implementation sessions landed in **v2.4.0 → v2.4.2** (cache + observability) and continued with rankings optimization.

### Production topology (as designed)

| Component | `wkpoule-prd` | `wkpoule-acc` | Notes |
|-----------|---------------|---------------|-------|
| API (`wkpoule-api`) | **2 replicas** | **1 replica** | 1 uvicorn process per pod (`opentelemetry-instrument uvicorn …`, no `--workers`) |
| Frontend (`wkpoule-frontend`) | **2 replicas** | **1 replica** | nginx static + `/api` proxy |
| PostgreSQL | 1 | 1 | Single writer; pool per API pod |
| Redis | 1 | 1 | `redis:6379`, AOF on 1Gi PVC |
| HPA | **None** | — | Fixed replica count in YAML |
| CPU/memory limits on app pods | **None** in base manifests | — | OTel collectors *do* have limits |

**Manifest paths:** `openshift/base/deployment-api.yaml`, `deployment-frontend.yaml`, `deployment-redis.yaml`, `deployment-postgres.yaml`. Apply prd: `oc apply -k openshift/`. Apply acc: `oc apply -k openshift/overlays/acc/`.

**Why 1 worker per pod (not `--workers 4`):** Each uvicorn worker is a full app copy → multiplied memory, Postgres connections, **score poller** instances, and in-memory weather cache. Preferred scale path: **more pods**, not more workers per pod.

### Phase implementation status

| Phase | Topic | Status | Version / notes |
|-------|--------|--------|-----------------|
| 1 | Redis on OpenShift (Deployment, Service, PVC) + `redis_*` in `config.py` | **Done** | v2.4.0; `fakeredis` in dev requirements |
| 2 | Cache module (`redis_client`, `service`, `keys`, `invalidation`) + `/api/health` redis field | **Done** | Fail-open if Redis down |
| 3 | Endpoint caching + write-path invalidation | **Done** | v2.4.0; see table below |
| 4 | OTel cache metrics + collector `redis` receiver + `redis-dashboard.json` | **Done** | `wkpoule.cache.*` metrics |
| 4b | Shared `rankings:all` for `/rankings` + `/rankings/me` | **Done** | v2.4.2; `rankings_cache.py` |
| 5 | Coverage 70% → 80%, load test script | **Partial / pending** | Cache unit tests exist; CI gate & `scripts/load-test.ts` not done |
| — | `asyncio.to_thread` for sync `compute()` in cache miss | **Not done** | Top-5 item #2 |
| — | HPA + 4–6 API pods | **Not done** | Top-5 item #3; discussed, YAML not committed |
| — | `SCORE_POLLER_ENABLED` (single poller pod) | **Not done** | Needed before scaling API replicas |
| — | Shared match cache (strip `user_id` from key) | **Not done** | Top-5 item #4 |
| — | SQL rankings + Redis stampede lock | **Not done** | Top-5 item #5 |

### Cached endpoints (Phase 3)

TTLs in `backend/app/cache/ttl.py`. Keys in `backend/app/cache/keys.py`.

| Endpoint | TTL | Cache key pattern |
|----------|-----|-------------------|
| `GET /api/rankings` | 60s | `wkpoule:rankings:all` (global; subgroup filter bypasses) |
| `GET /api/rankings/me` | 60s | Same shared `rankings:all` |
| `GET /api/matches` | 300s | `wkpoule:matches:list:…:user={id}` |
| `GET /api/matches/{id}` | 300s | `wkpoule:matches:detail:id=…:user={id}` |
| `GET /api/predictions/virtual-groups` | 120s | `wkpoule:predictions:virtual-groups:user={id}` |
| `GET /api/subgroups` (directory) | 60s | `wkpoule:subgroups:directory:user={id}` |
| `GET /api/subgroups/{id}` | 60s | per user + pagination |
| `GET /api/teams` | 3600s | `wkpoule:teams:list` |

**Invalidation** (`backend/app/cache/invalidation.py`):

- Score update (API sync or admin `PATCH …/score`) → `invalidate_on_score_update()` clears `rankings:*`, `matches:*`, `virtual-groups:*`
- Prediction upsert → `invalidate_on_prediction(user_id)` clears rankings + that user's virtual groups
- Subgroup membership/message changes → `invalidate_subgroup()` + directory pattern

Sync routes call `run_cache_task()` / `await invalidate_*` because sync DB handlers run off the main event loop; `set_main_event_loop()` in `main.py` lifespan schedules Redis work on the uvicorn loop.

### Rankings optimization (v2.4.2)

**Before:** `/api/rankings/me` on cache miss ran `compute_participant_rankings(db, None)` for **every user** — dashboard hit this on every load.

**After:** `get_cached_participant_rankings()` stores one list under `wkpoule:rankings:all`; `/rankings/me` uses `find_participant_ranking()`. One DB compute per 60s window serves all users.

**Rough capacity impact** (2 API pods, 1 worker each, architecture estimate not load-tested):

| Scenario | Pre-cache | Post-cache + shared rankings |
|----------|-----------|------------------------------|
| Comfortable concurrent browsers | ~50–150 | ~75–175 |
| Match-night standings spike | many full recomputes | 1 recompute / 60s then Redis reads |

Subgroup standings (`GET /api/subgroups/{id}` with embedded rankings) still compute per request on cache miss — weaker than global rankings.

### Observability (Phase 4)

- **App metrics** (`backend/app/cache/metrics.py`): `wkpoule.cache.hit`, `wkpoule.cache.miss`, `wkpoule.cache.operation.duration`, `wkpoule.redis.pool.connections`
- **Collector** (`openshift/base/otel-collector.yaml`): `redis` receiver on `redis:6379`, `metrics/redis` pipeline
- **Dashboard** (`openshift/redis-dashboard.json`): ES|QL panels for cache + Redis server metrics
- **Health:** `GET /api/health` → `{"status":"ok","redis":"ok"|"unavailable"}`

### Top 5 performance backlog (1 worker, more pods)

Ordered by impact; from capacity review session. **#1 done**; rest open.

| # | Change | Status | Agent notes |
|---|--------|--------|-------------|
| 1 | Shared `rankings:all` for `/rankings/me` | **Done** (2.4.2) | Do not reintroduce per-user full recompute |
| 2 | `asyncio.to_thread(compute)` in `cached_call` on miss | **Todo** | Sync SQLAlchemy blocks event loop today |
| 3 | Scale API 2 → 4–6 pods + HPA; poller on one pod only | **Todo** | Add `SCORE_POLLER_ENABLED` env before scaling |
| 4 | Shared match payload cache (user overlay in memory) | **Todo** | Keys currently include `user_id` → duplicate cold misses |
| 5 | SQL `SUM(prediction.points)` + Redis `SETNX` stampede guard | **Todo** | Reduces Postgres spikes when TTL expires after goals |

**Rejected for this pool size:** DB-level pagination for matches, splitting virtual-standings cache — negligible gain at 104 fixtures (see transcript `7bafecfa`).

### Deploy checklist (cache-related)

1. **Redis manifests** — `oc apply -k openshift/` (or acc overlay); verify `oc exec deploy/redis -- redis-cli ping` → `PONG`
2. **Rebuild API image** after `requirements.txt` / cache code changes — `oc start-build bc/wkpoule-api` (manifest apply alone does not update app code)
3. **Health** — `GET /api/health` must show `"redis":"ok"` on new pods
4. **Verify keys** — `redis-cli KEYS 'wkpoule:*'` after traffic; expect TTLs 60/120/300/3600s
5. **Invalidation** — after admin score or poller update, rankings/matches keys should disappear and repopulate

### Cache module map

```text
backend/app/cache/redis_client.py   # pool, OTel RedisInstrumentor, init/close
backend/app/cache/service.py        # get/set/delete_json, delete_pattern; fail-open
backend/app/cache/helpers.py        # cached_call, cached_call_async, run_cache_task
backend/app/cache/keys.py           # key builders
backend/app/cache/ttl.py            # TTL constants
backend/app/cache/invalidation.py # event-driven clears
backend/app/cache/metrics.py        # OTel counters/histograms
backend/app/services/rankings_cache.py  # shared global rankings list
```

**Tests:** `backend/tests/unit/cache/test_*.py`, `backend/tests/unit/test_rankings_cache.py`

### Frontend performance fix (related)

**Rankings pagination** (`rankings.slice` crash, ~v1.7): API returns `PaginatedResponse`; use `rankingsItems()` from `frontend/src/utils/rankings.ts` — never `.slice()` on raw API response.

---

## Domain invariants (do not regress)

### Knockout tip scoring uses 90-minute scores only

- `Match.home_score` / `Match.away_score` = goals after **90 minutes** (regular time).
- `Match.winner_team_id` = who **advanced** when level at 90 (extra time / penalties). Required for completed knockout draws.
- User predictions mirror this: equal `home_score`/`away_score` on knockout matches require `advance_team_id`.

### football-data.org v4 score shape

| Field | Meaning |
|-------|---------|
| `score.regularTime` | Goals after 90 min when match went to ET or pens |
| `score.fullTime` | **Running total** — after pens can be e.g. 7–6, not the 90-min result |
| `score.extraTime` / `score.penalties` | Segment scores only; **never** use for tip scoring |
| `score.winner` | Advancing side (`HOME_TEAM` / `AWAY_TEAM`) when decided after ET/pens |

**Rule:** Always read 90-min goals via `goals_at_90_from_api_score()` in `match_fixture_sync.py` (prefers `regularTime`, falls back to `fullTime`).

Docs: https://docs.football-data.org/general/v4/overtime.html

API keys may use `home`/`away` or `homeTeam`/`awayTeam` in score nodes — helper handles both.

### Admin score overrides are sacred

- `Match.score_overridden_by_admin` is set `true` on every admin `PATCH /api/matches/{id}/score`.
- `apply_score_from_api_match()` in `score_sync.py` **skips** `home_score`, `away_score`, and `winner_team_id` when flag is set.
- Status sync from API still runs; only scores/winner are protected.
- **Deploy note:** Matches corrected manually *before* this flag existed need one more admin save, or `UPDATE matches SET score_overridden_by_admin = true WHERE …`.

### Knockout bracket propagation

`compute_predicted_knockout_teams()` fills TBD knockout slots and validates advance picks. Rules:

1. **Completed** knockout match → winner from **actual** `home_score`/`away_score`/`winner_team_id` (`resolve_winner_team_id`).
2. **Upcoming** knockout match → winner from **user prediction** (`predicted_winner_team_id`).
3. **Fixture pair** → prefer `Match.home_team_id`/`away_team_id` from DB (API-assigned) over bracket-computed ids.

Group-stage feeders use `compute_virtual_group_standings()`: completed group matches use real scores; unplayed use predictions.

### Status mapping during sync

`EXTRA_TIME` and `PENALTY_SHOOTOUT` map to `in_progress`. Scores are applied only when status becomes `completed` (`FINISHED`). Do not apply `fullTime` while match is still in ET/pens.

---

## Bug history (symptoms → cause → fix)

### 1. Knockout scores wrong after ET / penalties (v2.7.1)

**Symptom:** Synced knockout scores reflected extra time or penalty totals (e.g. 7–6) instead of 90-minute results (e.g. 1–1).

**Cause:** `score_sync.py` read `score.fullTime`. In football-data.org v4, `fullTime` is a running total after ET/pens.

**Fix:**
- Added `goals_at_90_from_api_score()` in `match_fixture_sync.py`.
- Refactored sync through `apply_score_from_api_match()` in `score_sync.py`.

**Tests:** `backend/tests/unit/test_match_fixture_sync.py`, `backend/tests/unit/test_score_sync.py`

---

### 2. Admin scores overwritten by API sync (v2.7.1)

**Symptom:** Admin corrected a score in Admin UI; next football-data.org poll reverted it.

**Cause:** No guard in `sync_scores()`; every completed match was updated from API.

**Fix:**
- Column `matches.score_overridden_by_admin` (`backend/app/models/match.py`).
- Migration in `backend/app/db_schema.py` (Postgres + SQLite paths).
- Set flag in `update_score()` (`backend/app/routers/matches.py`).
- Early return in `apply_score_from_api_match()` when flag is true.

**Tests:** `test_apply_score_from_api_match_skips_admin_override`, `test_admin_score_update` sets flag.

---

### 3. Next knockout round shows predicted winner, not actual (v2.7.2)

**Symptom:** Round of 16 showed Netherlands (user's R32 tip) after Morocco actually won R32.

**Cause:** `bracket_resolver.py` used `win_from_pred()` for **all** rounds — always `predicted_winner_team_id()` from user tips, even when feeder match was `completed`.

**Fix:** Replaced with `winner_for_fixture()`:
- Completed → `resolve_winner_team_id()` on match record.
- Upcoming → prediction path unchanged.
- Added `fixture_pair()` to prefer DB-assigned teams.

**Consumers (all must stay consistent):**
- `GET /api/matches?predicted_teams=true`
- `resolve_fixture_team_ids()` in `prediction_advance.py` (knockout draw validation)

**Tests:** `test_completed_knockout_uses_actual_winner_for_next_round` in `backend/tests/unit/test_bracket_knockout.py`

**Example:** R16 match 90 home slot = winner of match 73 (`R16_SOURCES[90] == (73, 75)`). After MAR beats NED in #73, slot must be MAR regardless of user's 73 prediction.

---

### 4. Knockout pen shootout progressor points wrong (v2.7.3 → v2.7.4)

**Symptom:** User tipped 1-1 with correct progressor (e.g. Egypt after pens vs Australia) but received **9** points instead of **12**.

**Cause (two parts):**
1. Score sync mapped API home/away incorrectly when DB fixture order differed (v2.7.3).
2. football-data.org can return `score.winner: null` after a shootout even when `duration` is `PENALTY_SHOOTOUT` (AUS vs EGY: pens 4-4, `fullTime` 3-5). Sync never set `winner_team_id` → no +3 bonus.

**Fix (v2.7.3):** orientation-aware match lookup and goal/winner mapping.

**Fix (v2.7.4):** `advancing_team_id_from_api_score()` — when `winner` is null after a level 90+ET score, infer progressor from decisive `penalties`, else from `fullTime` when duration is `PENALTY_SHOOTOUT` / `EXTRA_TIME`.

**Tests:** `test_advancing_team_id_from_api_score_egy_aus_null_winner_uses_full_time`, `test_apply_score_null_api_winner_infers_progressor_from_full_time`.

---

### 5. Rankings `.slice is not a function` (earlier session, ~v1.7.0 → fixed before v2.5)

**Symptom:** `Uncaught TypeError: rankings.slice is not a function` on Dashboard (production APM).

**Cause:** Backend returned paginated `{ items, total, page, … }`; frontend still treated `rankings` as an array.

**Fix:** `frontend/src/utils/rankings.ts` — `rankingsItems()`, `normalizeRankingsResponse()`. Updated `Dashboard.tsx`, `Rankings.tsx`, `SubgroupDetail.tsx`.

**Rule:** Any new rankings consumer must use `rankingsItems()`, not `.slice()` on the raw response.

**Tests:** `frontend/src/utils/rankings.test.ts`

---

## Regression checklist

When touching knockout, sync, or cache code, verify:

- [ ] ET/pens fixture: API payload with `regularTime: 1-1`, `fullTime: 7-6` → DB stores `1-1`, `winner_team_id` from API `winner`.
- [ ] Swapped API/DB home-away: same fixture still gets correct 90-min scores and `winner_team_id`; knockout draw tip with correct progressor → **12** points after recalc.
- [ ] Regular-time finish: no `regularTime` → `fullTime` used.
- [ ] Admin override: flag set on PATCH; sync does not change scores/winner.
- [ ] Bracket: completed feeder → next round uses actual winner; upcoming feeder → prediction.
- [ ] Knockout draw prediction still requires `advance_team_id` with resolved fixture teams.
- [ ] Frontend rankings: use `rankingsItems()` / `PaginatedResponse<T>`.
- [ ] Cache miss on rankings: only one `compute_participant_rankings` per TTL (shared `rankings:all`).
- [ ] Score/prediction writes: invalidation runs (rankings + matches + virtual-groups as appropriate).
- [ ] `/api/health` reports redis status after deploy.

---

## Key functions (quick lookup)

```text
get_cached_participant_rankings(db)   # rankings_cache.py — shared global list
cached_call / cached_call_async       # cache/helpers.py — read-through cache
invalidate_on_score_update()          # cache/invalidation.py
goals_at_90_from_api_score(score)     # match_fixture_sync.py — 90-min goals from API
apply_score_from_api_match(...)       # score_sync.py — apply to Match; respects admin flag
resolve_winner_team_id(...)           # scoring.py — winner from 90-min score + optional stored winner
compute_predicted_knockout_teams(...) # bracket_resolver.py — bracket fill + propagation
predicted_winner_team_id(...)         # knockout_winner.py — winner from *prediction* only
rankingsItems(...)                    # frontend — safe array from paginated rankings
```

---

## Testing

```bash
# From repo root (requires pytest in API image or local venv)
cd backend
pytest tests/unit/cache/ tests/unit/test_rankings_cache.py \
       tests/unit/test_match_fixture_sync.py tests/unit/test_score_sync.py \
       tests/unit/test_bracket_knockout.py -v

# Frontend rankings helper
cd frontend && npm test -- rankings.test.ts
```

Local Docker API image may lack pytest; use `pip install -r requirements-dev.txt` locally or CI.

---

## Related docs

| Doc | Use for |
|-----|---------|
| `docs/AGENTS.md` | Login, prediction API, endpoints |
| `llms.txt` | Short agent entry point |
| `docs/redis-caching-observability-test-coverage-plan.md` | Original phased plan; Phase 5 + some backlog items still open |

---

## Out of scope for this file

OKD cluster operations (etcd, VM placement, upgrades, build `nodeSelector` patches applied live on cluster) — not application code; cluster-specific runbooks live outside this repo.
