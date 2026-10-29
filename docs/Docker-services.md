## 1) Services in docker-compose

| Service | Purpose | Image source |
|---|---|---|
| `fake-gcs` | GCS emulator, DVC remote local testing | prebuilt image |
| `mlflow` | Tracking server + model registry UI | prebuilt image (or thin custom) |
| `registry` | Docker registry, local image push/pull | prebuilt image |
| `app` | FastAPI serving | **your Dockerfile** |
| `prometheus` | Scrapes `app` `/metrics` | prebuilt image, config file mounted |
| `grafana` | Dashboards over Prometheus | prebuilt image, config mounted |
| `airflow-db` | Postgres backend for Airflow | prebuilt image |
| `airflow-init` | One-shot: `airflow db migrate` + creates the admin user | **custom Dockerfile** (`infra/airflow/Dockerfile`) |
| `airflow-webserver` | Airflow UI + REST API | **custom Dockerfile** (`infra/airflow/Dockerfile`) |
| `airflow-scheduler` | Runs `retrain_dag` / `drift_dag` tasks | **custom Dockerfile** (`infra/airflow/Dockerfile`) |

Feast's online store is SQLite (file-based), not Redis — `infra/docker-compose.feast.yml` (a Redis service) is unused.

Not services (run as one-off containers or jobs, not long-running): `dvc repro`, `train.py`, `evaluate.py`, Evidently drift script, `feast apply`/`materialize-incremental`. These run via `docker compose run`, `act`, or inside an Airflow task, not `up`.

## 2) Which need a Dockerfile

**`app`** and the three Airflow services (`airflow-init`, `airflow-webserver`, `airflow-scheduler`, all built from `infra/airflow/Dockerfile`) need a custom Dockerfile.

Everything else (`fake-gcs`, `mlflow`, `registry`, `prometheus`, `grafana`, `airflow-db`) uses **official prebuilt images**, no Dockerfile, just `image:` line + config mount.

Optional second custom Dockerfile: a **`train` image** if you want training to run inside a container matching prod deps exactly (recommended for parity with GitHub-hosted runner containers). Call it `Dockerfile.train` or `infra/train.Dockerfile`.

So realistically: 1 required Dockerfile (`app`), 1 optional (`train`).

## 3) Linking Dockerfile to service in compose

```yaml
services:
  fake-gcs:
    image: fsouza/fake-gcs-server:1.47.4
    command: ["-scheme", "http", "-public-host", "fake-gcs"]
    ports: ["4443:4443"]

  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.17.2
    command: >
      mlflow server --host 0.0.0.0 --port 5000
      --backend-store-uri sqlite:///mlflow.db
      --default-artifact-root /mlruns
    ports: ["5000:5000"]
    volumes: ["mlflow-data:/mlruns"]

  registry:
    image: registry:2
    ports: ["5001:5000"]

  app:
    build:
      context: .              # repo root (needs src/, app/, requirements.txt)
      dockerfile: Dockerfile   # <- link here
    ports: ["8000:8000"]
    depends_on: [mlflow]
    environment:
      MLFLOW_TRACKING_URI: http://mlflow:5000

  prometheus:
    image: prom/prometheus:v2.55.0
    volumes: ["./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"]
    ports: ["9090:9090"]
    depends_on: [app]

  grafana:
    image: grafana/grafana:11.2.2
    ports: ["3000:3000"]
    depends_on: [prometheus]
```

Link mechanism: `build.context` + `build.dockerfile` fields under the service — compose builds image from that Dockerfile instead of pulling. `context` sets the build root so `COPY src/ ./src/` etc. resolve correctly; Dockerfile path relative to `context` unless you give absolute path.

For optional `train` image, same pattern, different key:
```yaml
  train:
    build:
      context: .
      dockerfile: infra/train.Dockerfile
    profiles: ["train"]   # so `docker compose up` skips it by default, run via `docker compose run train`
```