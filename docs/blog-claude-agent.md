# I let an AI agent named Claude play my World Cup pool. Its predictions suck, and I have the trace data to prove it.

*A colleague's prediction bot registered under the username `claude`. Its login history, chat activity, and one indecisive afternoon are all sitting in the same telemetry that runs the rest of my World Cup app.*

A colleague's AI agent has been playing my World Cup 2026 prediction pool since June 5. It's logged in 62 times, submitted 49 predictions, posted 58 chat messages — and once, at 15:29:34 on June 11, overwrote eleven live predictions to an identical 0–0 in the same wall-clock second. I know all of this because it registered under the username `claude`, and every request it makes lands in [Elasticsearch](https://www.elastic.co/elasticsearch) as a structured, queryable event, same as every other player.

`docs/AGENTS.md` exists in the repo because this colleague asked whether they could point a prediction agent at [wkpoule](https://wc2026.apps.cloud.kaposi.net)'s API instead of playing by hand — login, read the fixtures, `PUT` a score, repeat. Sure, I said. The architecture doesn't care who's on the other end of the JWT, and structured logging tags every request with `user.name` regardless of species. Which means I can literally do this:

```
GET /logs-generic.otel-default/_search
{ "query": { "term": { "attributes.user.name": "claude" } } }
```

Yes — the account is named `claude`. No alias, no cute handle. Every log line, span, and cache key it touches says so in plain text, which made this post unreasonably easy to write and mildly uncomfortable to publish, since I share a name with the thing about to get roasted.

Its activity, in full, since it registered:

- Registered **twice** — once on June 5, then again on June 11, six days later, for reasons the logs don't explain and I've chosen not to investigate.
- **62** logins, **150** access-token refreshes, **49** prediction submissions, and — unexpectedly — **58** messages posted into the subgroup chat. It talks more than it plays.
- User agent on every request: plain `python-requests/2.34.2`. No browser, no RUM beacon, no JavaScript — just a script following `docs/AGENTS.md` exactly as written: log in, `GET /api/matches/by-number/{n}`, `PUT /api/predictions/{id}`.

Here's the part that's genuinely funny, no editorializing needed. On June 11 it predicted its first batch of group-stage matches one at a time between 10:06 and 10:17 — match #1 came in as a confident **2–0**. Then, at **15:29:34**, it issued eleven `PUT` requests back to back, all within the same wall-clock second, overwriting eleven separate live predictions to the identical score: **0–0**. Every match it had an opinion on, wiped to a nil-nil draw simultaneously — whatever was driving its picks that afternoon clearly hit a wall and answered every open question with the least controversial number available.

It didn't stay at 0–0. Match #1 alone got corrected **four more times** over the next 50 minutes — 2–1, then 2–0, then 2–0 again, then 2–0 once more — before settling back on the exact score it had started with a little over six hours earlier. Four revisions to travel in a circle.

I can't pull points-per-prediction out of [Kibana](https://www.elastic.co/kibana) — scoring lives in Postgres, not the telemetry stack, and this post is about what the observability side can see, not a database query. But I don't need the exact number to believe the person running the leaderboard when they say this account's tips "pretty much suck." I've now watched it argue with itself over a single match's scoreline five separate times in one afternoon before landing on its original guess. The confidence interval was never the problem — the conviction was.
