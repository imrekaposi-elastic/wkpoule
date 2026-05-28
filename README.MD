I want to have a world cup game prediction website.
- Only registered users can participate. Use secure login routine
- Status of site is persistent. It should survive reboots
- All games of world cup 2026 need to be predicted by the user.
    - Correct result: 3 points
    - Correct score: 8 points
    - Correct number of goals: 1 point
- The site should automatically translate scores to group rankings
- per match this info is presented:
    - date & time
    - home team
    - away team
    - venue & capacity
    - expected temperature during match in celsius
    - A fun but irrelevent comment in the expert prediction box. It should be in the style of Donald Trump or Bill Burr and should write something about either the venue, the city, the teams or some historical match between them before
    - Based on previous results of the teams and the current worldcup ranking, there should be an expert prediction suggestion
- the predictions of other participants are visible by all registered users
- There should be a ranking page of participants
- the website and storage will be hosted on openshift

## Tests and CI

- **Backend** (pytest): unit tests for scoring, auth, prediction lock, bracket logic; integration tests for HTTP API (`backend/tests/`). Run locally: `make test-backend` or `cd backend && pytest`.
- **Frontend** (Vitest): unit tests under `frontend/src/**/*.test.ts`. Run locally: `make test-frontend` or `cd frontend && npm run test:ci`.
- **GitHub** (`.github/workflows/`): runs on every push/PR to `main` — see the [Actions tab](https://github.com/imrekaposi-elastic/wkpoule/actions).
- **GitLab** (`.gitlab-ci.yml`): same jobs if you mirror the repo to GitLab.

## Repository layout (containers)

- **`backend/`** — FastAPI API image (`Dockerfile`, context = this directory only).
- **`frontend/`** — React SPA + nginx reverse proxy for `/api` (`Dockerfile`, context = this directory only).
- **`docker-compose.yml`** — local stack: Postgres + API + frontend (three containers).
- **`openshift/`** — Kustomize manifests + [`openshift/README.md`](openshift/README.md) (three runtimes, monorepo build hints).
