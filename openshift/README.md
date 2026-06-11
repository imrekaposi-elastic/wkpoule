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

So: **two app images**, no “fat” image; the browser hits the frontend Route; the API is also exposed on a **dedicated Route** for direct access.

### Public hostnames

| Route | Hostname | Service |
|-------|----------|---------|
| `wkpoule` | `wc2026.apps.cloud.kaposi.net` (prd) / `acc-wc2026…` (acc) | `wkpoule-frontend` (SPA + nginx `/api` proxy) |
| `wkpoule-api` | `wc2026-api.apps.cloud.kaposi.net` (prd) / `acc-wc2026-api…` (acc) | `wkpoule-api` (FastAPI, `/docs`, `/openapi.json`) |

Set **`PUBLIC_APP_URL`** (SPA) and **`PUBLIC_API_URL`** (API) in [`secret.yaml`](secret.yaml) to match these hosts. Agent documentation: [`docs/AGENTS.md`](../docs/AGENTS.md).

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

## Observability (EDOT + exceptions)

**EDOT / OpenTelemetry (Elastic guidance for ECE):**

Topology matches [Kubernetes environments](https://www.elastic.co/docs/reference/opentelemetry/architecture/k8s): **edge** DaemonSet + cluster collector → **in-cluster gateway** → **Elasticsearch**, using the same **`elasticsearch/otel`** exporter pattern as the backend EDOT gateway on otl01 (OTel-native mapping, API key).

- **In-cluster gateway:** [`otel-collector.yaml`](otel-collector.yaml) `OpenTelemetryCollector/wkpoule-otel` receives OTLP from apps ([`observability-config.yaml`](observability-config.yaml)), infra, and cluster collectors; enriches traces/logs with **`k8sattributes` + `elasticapm`** (DB client spans get `peer.service=postgresql` for service-map correlation); exports with **`elasticsearch/otel`** to **`ELASTICSEARCH_URL`** and **`ELASTIC_API_KEY`** (see also [`scripts/edot-backend/backend-host-observed.txt`](../scripts/edot-backend/backend-host-observed.txt)).
- **Edge DaemonSet:** [`otel-k8s-infra.yaml`](otel-k8s-infra.yaml) ships kubelet metrics and **wkpoule-prd container stdout** (frontend nginx ECS JSON via `filelog`; API logs stay on OTLP) OTLP **to the gateway** Service `wkpoule-otel-collector:4318`. Requires **`/var/log/pods` hostPath** (OpenShift: often `hostaccess` or `privileged` SCC on the collector pod).
- **Cluster collector:** [`otel-k8s-cluster.yaml`](otel-k8s-cluster.yaml) runs **`k8s_cluster`** (`distribution: openshift`) and sends OTLP **to the same gateway**. RBAC: [`rbac-otel-cluster.yaml`](rbac-otel-cluster.yaml). **Only one** `k8s_cluster` replica per cluster.
- **Gateway RBAC:** [`rbac-otel-gateway.yaml`](rbac-otel-gateway.yaml) — ServiceAccount `wkpoule-otel-gateway` for `k8sattributes` API reads in the namespace.

**Legacy / exceptions:**

- **RUM:** Browser → APM Server URL via nginx (see [`observability-config.yaml`](observability-config.yaml)).

PostgreSQL observability uses the [PostgreSQL OpenTelemetry Assets](https://www.elastic.co/docs/reference/integrations/postgresql_otel) integration only (`postgresqlreceiver` in [`otel-collector.yaml`](otel-collector.yaml)). The canonical **OTel/APM service name is `postgresql`** (receiver metrics, dependencies via `elasticapm`); the K8s Deployment/Service and `DATABASE_URL` host remain **`postgres`**.

Redis observability uses the [Redis OpenTelemetry Assets](https://www.elastic.co/docs/reference/integrations/redis_otel) integration (`redis` receiver on the `metrics/redis` pipeline in [`otel-collector.yaml`](otel-collector.yaml)). Install the integration dashboards/alerts in Kibana, and use [`redis-dashboard.json`](redis-dashboard.json) for application cache ES|QL panels (`wkpoule.cache.*`, `wkpoule.redis.pool.connections`). The API exports cache hit/miss, operation latency, and pool gauges via OTLP; Redis server metrics (memory, keyspace hits, command latency) come from the collector receiver scraping `redis:6379`.

Ensure OpenShift **egress** allows the **gateway** Deployment to reach **`ELASTICSEARCH_URL`** on `443`. Edge components keep using **`http://wkpoule-otel-collector:4318`** unless you rename the gateway Service. If TLS verification fails against ECE (hostname vs cert SAN), adjust [`otel-collector.yaml`](otel-collector.yaml) `elasticsearch/otel` `tls` or fix the deployment URL/certificate.

**Public hostnames:** Set [`route.yaml`](route.yaml) / [`route-api.yaml`](base/route-api.yaml) `spec.host` values and the matching **`PUBLIC_APP_URL`** / **`PUBLIC_API_URL`** in [`secret.yaml`](secret.yaml) so invite links, OpenAPI servers, and CORS stay aligned — see [`deploy.md`](../deploy.md) §7.

## PostgreSQL backups

[`cronjob-postgres-backup.yaml`](cronjob-postgres-backup.yaml) runs **`pg_dump`** every 12 hours (`0 */12 * * *`) and stores custom-format dumps on [`pvc-postgres-backup.yaml`](pvc-postgres-backup.yaml). The job keeps the **14** newest files (~7 days). Dumps are **not** stored in a ConfigMap (1 MiB limit; wrong tool for backup data).

Manual backup run:

```bash
oc create job --from=cronjob/wkpoule-postgres-backup wkpoule-postgres-backup-manual-$(date +%s)
```

### Verify backups exist (OKD / restricted PSA)

Do **not** use `oc run` with `busybox` — it runs as root and triggers **PodSecurityViolation** on OKD.

**1. Job logs** (easiest; backup job lists `/backups` at the end):

```bash
oc get jobs | grep postgres-backup
oc logs job/<job-name>
```

Look for `Dump complete (... bytes)` and `ls -lah /backups` output.

**2. List Job** (same image + security profile as the CronJob):

```bash
oc delete job wkpoule-postgres-backup-ls --ignore-not-found
oc apply -f openshift/job-postgres-backup-ls.yaml
oc logs -f job/wkpoule-postgres-backup-ls
```

**3. CronJob status:**

```bash
oc get cronjob wkpoule-postgres-backup
```

Re-apply the stack after changing the CronJob (`oc apply -k openshift/`). New dumps use `chmod 644` so the list Job can read files written by another pod UID.

Copy a dump off-cluster: run a short-lived pod from [`job-postgres-backup-ls.yaml`](job-postgres-backup-ls.yaml) with `sleep 3600` instead of `ls`, then `oc cp` from that pod (postgres image, not busybox).
