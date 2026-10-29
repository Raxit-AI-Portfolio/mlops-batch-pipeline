```text

mlops-batch-pipeline/
├── .github/
│   └── workflows/
│       ├── ci.yml                  # PR: lint, unit tests, data gate
│       ├── train.yml               # dvc pull/repro, MLflow, baseline gate
│       ├── register-deploy.yml     # register model, build image, deploy, trigger retrain_dag
│       ├── drift.yml               # workflow_dispatch: Evidently report
│       └── feast-apply.yml         # feast plan/apply/materialize
│
├── .dvc/                           # DVC config (remote per profile)
├── dvc.yaml                        # stages: validate → train → evaluate
├── params.yaml                     # hyperparams, thresholds, tolerance
├── dvc.lock
│
├── data/
│   └── raw/                        # DVC-tracked (iris.csv)
│
├── src/
│   └── mlcicd/
│       ├── config.py               # reads env vars, profile-aware
│       ├── data/
│       │   ├── load.py
│       │   └── schema.py           # pandera schemas
│       ├── features/
│       │   └── build.py            # shared train/serve feature logic
│       ├── training/
│       │   ├── train.py
│       │   └── evaluate.py         # compare vs baseline, exit 1 on regression
│       ├── registry/
│       │   └── register.py         # MLflow register if gate passes
│       └── monitoring/
│           ├── drift.py            # Evidently
│           └── post_deploy_check.py # confirm version scraped by Prometheus
│
├── app/                            # FastAPI serving
│   ├── main.py
│   ├── model_loader.py             # load from MLflow registry
│   ├── schemas.py                  # request/response models
│   └── metrics.py                  # Prometheus, model_version gauge
│
├── orchestration/
│   └── dags/
│       ├── retrain_dag.py          # @daily: train → evaluate → register, via the same CLI entrypoints as GHA
│       └── drift_dag.py            # @daily: mlcicd.monitoring.drift
│
├── feature_repo/                   # Feast
│   ├── feature_store.local.yaml    # file/Dask offline + SQLite online
│   ├── feature_store.gcp.yaml      # BigQuery offline + Datastore online (config only, not yet applied)
│   ├── entities.py                 # iris_id entity
│   ├── feature_views.py            # iris_features view
│   └── main.py                     # builds the offline-source parquet from data/raw/iris.csv
│
├── tests/
│   ├── data/                       # schema, nulls, ranges, leakage
│   ├── unit/                       # feature/preprocess functions
│   ├── model/
│   │   ├── test_pretrain.py        # shape, overfit-one-batch, no NaN
│   │   ├── test_posttrain.py       # invariance, directional, slices
│   │   └── test_calibration.py     # predicted probabilities vs empirical accuracy
│   ├── regression/                 # baseline metrics, golden-set stability, run-to-run reproducibility
│   ├── infra/                      # DVC stage graph / params / profile loading
│   ├── serving/                    # API contract, model loads from registry, latency budget
│   └── feast/                      # online/offline parity
│
├── baselines/
│   └── metrics_baseline.json       # tracked baseline
│
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/                    # provisioned dashboards
│
├── infra/
│   ├── docker-compose.yml          # fake-gcs, mlflow, registry, app, prometheus, grafana, airflow-*
│   ├── docker-compose.feast.yml    # unused — Feast's online store is SQLite, not Redis
│   ├── airflow/
│   │   └── Dockerfile              # extends apache/airflow, installs requirements.txt + mlcicd
│   └── gcp/                        # Terraform: bucket, Artifact Registry, Cloud Run, WIF, secrets
│
├── profiles/
│   ├── local.env                   # act + compose endpoints
│   ├── github.env                  # CI
│   ├── prod.env                    # GCP/DagsHub
│   └── onprem.env                  # stub, no GCP refs
│
├── .actrc                          # act runner image, network flags
├── .secrets.local.example          # act/Airflow secrets template (real file gitignored)
├── Dockerfile                      # app image, pulls model from registry at build
├── Makefile                        # up, down, repro, test, feast-apply, feast-materialize, etc.
├── pyproject.toml                  # deps, pytest markers, ruff config
├── requirements.txt / requirements-dev.txt
├── .gitignore / .dvcignore
└── README.md                       # architecture, how to run local vs GCP

```
