# OpenShift layout (monorepo, three runtimes)

This folder deploys **three separate container workloads**. None of them use the repository root as a Docker build context.

| Runtime | Image source | Build context (Git) | K8s workload |
|--------|--------------|---------------------|--------------|
| **PostgreSQL** | `docker.io/library/postgres:16-alpine` | *(none — pull only)* | `deployment-postgres.yaml` |
| **API** | Your registry / `wkpoule-api` | **`backend/`** only | `deployment-api.yaml` |
| **Frontend** | Your registry / `wkpoule-frontend` | **`frontend/`** only | `deployment-frontend.yaml` |

## Why the frontend talks to the API

- The SPA uses `axios` with `baseURL: "/api"` ([`frontend/src/api/client.ts`](../frontend/src/api/client.ts)).
- **Local / OpenShift (single Route):** nginx in the frontend container proxies `/api/*` to the cluster Service `wkpoule-api:8000` via env **`API_HOST`** ([`frontend/nginx.conf`](../frontend/nginx.conf), [`deployment-frontend.yaml`](deployment-frontend.yaml)).
- **Vite dev server:** proxies `/api` to `localhost:8000` ([`frontend/vite.config.ts`](../frontend/vite.config.ts)).

So: **two app images**, no “fat” image; the browser only hits the Route host; API is not mixed into the static build.

## Building images from this monorepo

**Images only (recommended with this repo’s YAML):** use **BuildConfigs** that output to `wkpoule-api:latest` and `wkpoule-frontend:latest`. Do **not** use `oc new-app` for the API/frontend if you already apply [`deployment-api.yaml`](deployment-api.yaml) / [`deployment-frontend.yaml`](deployment-frontend.yaml) — `new-app` would duplicate Deployments. Step-by-step: [`deploy.md`](../deploy.md) §6, subsection *Images only*.

From your laptop (push to registry manually):

```bash
make build-all
```

Or:

```bash
docker build -t wkpoule-api:latest -f backend/Dockerfile backend
docker build -t wkpoule-frontend:latest -f frontend/Dockerfile frontend
```

On OpenShift, use **Git `contextDir`** — [`examples/buildconfigs-git.yaml`](examples/buildconfigs-git.yaml) (HTTPS) or [`examples/buildconfigs-git-ssh.yaml`](examples/buildconfigs-git-ssh.yaml) with a `kubernetes.io/ssh-auth` Secret — or Tekton with an SSH workspace. Full SSH steps: [`deploy.md`](../deploy.md) §4.

## Apply manifests

```bash
oc apply -k openshift/
```

Adjust `namespace` in [`kustomization.yaml`](kustomization.yaml) and image stream paths in the Deployments if your project name is not `wkpoule-prd`.

**Public hostname:** Set [`route.yaml`](route.yaml) `spec.host` and the same URL (with `https://`) as **`PUBLIC_APP_URL`** in [`secret.yaml`](secret.yaml) so invite links and CORS stay aligned — see [`deploy.md`](../deploy.md) §7.
