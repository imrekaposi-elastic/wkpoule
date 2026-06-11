# WK Poule API — Agent Guide

This document describes how automated agents (e.g. Claude) can authenticate, discover matches, and post predictions against the WK Poule World Cup 2026 API.

## Base URLs

| Environment | API base URL | Web app (SPA) |
|-------------|--------------|---------------|
| Production | `https://wc2026-api.apps.cloud.kaposi.net` | `https://wc2026.apps.cloud.kaposi.net` |
| Acceptance | `https://acc-wc2026-api.apps.cloud.kaposi.net` | `https://acc-wc2026.apps.cloud.kaposi.net` |

All API routes are under `/api/…`. The SPA proxies `/api` through nginx; agents should call the **dedicated API hostname** above.

### Machine-readable spec

| Resource | URL |
|----------|-----|
| OpenAPI JSON | `{base}/openapi.json` |
| Swagger UI | `{base}/docs` |
| ReDoc | `{base}/redoc` |
| Health | `{base}/api/health` |

## Authentication

1. **Login** — `POST /api/auth/login` with JSON body:

   ```json
   { "username": "your_username", "password": "your_password" }
   ```

2. **Response** — save both tokens:

   ```json
   {
     "access_token": "<jwt>",
     "refresh_token": "<jwt>",
     "token_type": "bearer"
   }
   ```

3. **Authenticated requests** — add header on every protected call:

   ```
   Authorization: Bearer <access_token>
   ```

4. **Token lifetime** — access tokens expire after **30 minutes**. Refresh with:

   ```
   POST /api/auth/refresh
   { "refresh_token": "<refresh_token>" }
   ```

5. **Register** (if you need a new account) — `POST /api/auth/register`:

   ```json
   {
     "username": "agent_bot",
     "email": "bot@example.com",
     "password": "secure-password",
     "preferred_language": "en"
   }
   ```

## Posting predictions (primary workflow)

### Step 1 — Find the match

Matches have two identifiers:

| Field | Meaning | Example |
|-------|---------|---------|
| `match_number` | FIFA schedule number (1–104) | `42` |
| `id` | Database primary key (used in prediction URL) | `87` |

Resolve by schedule number:

```
GET /api/matches/by-number/{match_number}
Authorization: Bearer <access_token>
```

Read `id` from the response — that is the `match_id` for predictions.

Alternatively, list upcoming fixtures:

```
GET /api/matches?status=upcoming
GET /api/matches/next-needing-prediction
```

### Step 2 — Submit prediction

```
PUT /api/predictions/{match_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "home_score": 2,
  "away_score": 1,
  "advance_team_id": null
}
```

| Field | Type | Notes |
|-------|------|-------|
| `home_score` | int 0–20 | Required |
| `away_score` | int 0–20 | Required |
| `advance_team_id` | int or null | Required when predicting a **draw in a knockout match** (penalty winner) |

### Step 3 — Verify

```
GET /api/predictions/mine/brief
```

Returns all your tips as `{ match_id, home_score, away_score, advance_team_id }`.

## Prediction rules

The API enforces these rules on `PUT /api/predictions/{match_id}` (the only way to create or change a tip; there is no delete endpoint):

- Match `status` must be `"upcoming"`. **Live** and **completed** matches return `400`.
- Predictions **lock 30 minutes before kickoff** (UTC). After kickoff, create/update is also rejected even if status has not updated yet.
- Check `prediction_editable` on `GET /api/matches/{match_id}` before submitting — when `false`, do not call `PUT`.
- Knockout draws: set equal scores **and** `advance_team_id` to the team you predict advances on penalties.
- Scores are integers from 0 to 20.

## Common endpoints

### Matches

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/matches` | List matches (filterable) |
| `GET` | `/api/matches/by-number/{n}` | Resolve match by FIFA number |
| `GET` | `/api/matches/{match_id}` | Single match by database id |
| `GET` | `/api/matches/next-needing-prediction` | Next fixture without your tip |
| `GET` | `/api/matches/calendar-meta` | Calendar metadata |

### Predictions (all require auth)

| Method | Path | Description |
|--------|------|-------------|
| `PUT` | `/api/predictions/{match_id}` | Create/update prediction |
| `GET` | `/api/predictions/mine` | Your predictions (paginated) |
| `GET` | `/api/predictions/mine/brief` | All your tips (compact) |
| `GET` | `/api/predictions/match/{match_id}` | All predictions for a match |

### Reference data

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/teams` | All teams |
| `GET` | `/api/teams/{fifa_code}` | Team by FIFA code (e.g. `NED`) |
| `GET` | `/api/venues` | All venues |
| `GET` | `/api/rankings` | Leaderboard |
| `GET` | `/api/rankings/me` | Your ranking |

## Example session (curl)

```bash
BASE=https://acc-wc2026-api.apps.cloud.kaposi.net

# Login
TOKENS=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","password":"mypass"}')
TOKEN=$(echo "$TOKENS" | jq -r .access_token)

# Resolve match 42 → database id
MATCH=$(curl -s "$BASE/api/matches/by-number/42" \
  -H "Authorization: Bearer $TOKEN")
MATCH_ID=$(echo "$MATCH" | jq -r .id)

# Post prediction
curl -s -X PUT "$BASE/api/predictions/$MATCH_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"home_score":2,"away_score":1,"advance_team_id":null}'
```

## Error responses

| Status | Typical cause |
|--------|---------------|
| `401` | Missing or expired token |
| `404` | Match not found |
| `400` | Match locked, invalid scores, or missing `advance_team_id` on knockout draw |

Error body: `{ "detail": "human-readable message" }`.

## Pagination

List endpoints that return many items use `?page=1&page_size=50` (default page size: 50).

## Notes for agent implementers

- Always use the **database `id`**, not `match_number`, in `PUT /api/predictions/{match_id}`.
- Prefer the acceptance API (`acc-wc2026-api`) for testing.
- Fetch `/openapi.json` for the complete, up-to-date schema including request/response models.
- The web app URL and API URL are different; do not substitute one for the other.
