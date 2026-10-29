# Scripts

PowerShell scripts to bring the project up and down, locally and on GCP, without editing any file between runs. Run them from the repo root.

| Environment | Up | Down |
|---|---|---|
| Local (Docker) | `local-up.ps1` | `local-down.ps1` |
| Remote (GCP) | `gcp-up.ps1` | `gcp-destroy.ps1` |

`common.ps1` is a shared helper file (`Invoke-Native`, `Confirm-Step`, `Get-LocalSetting`, `Backup-State`). Do not run it directly.

If PowerShell blocks the scripts, allow them for the current window only:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

---

## 1. Local Environment

Runs the full stack on your machine with Docker Compose: MLflow (model registry), fake GCS, a local Docker registry, the FastAPI app, Prometheus and Grafana.

### Pre-requisites
- Docker Desktop running.
- Project virtual environment `.venv` with the project installed:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
  .\.venv\Scripts\pip install -e .
  ```
- Training data present locally (`data/raw/iris.csv`, restored with `dvc pull` if needed).
- Free ports: 3000 (Grafana), 4443 (fake GCS), 5000 (MLflow), 5001 (image registry), 8000 (API), 9090 (Prometheus).
- Optional, for the prediction page: a separate `.venv-ui` (Streamlit conflicts with the FastAPI pins in `.venv`):
  ```powershell
  .\.venv\Scripts\python.exe -m venv .venv-ui
  .\.venv-ui\Scripts\pip install -r ui/requirements.txt
  ```

### local-up.ps1
```powershell
.\scripts\local-up.ps1              # -SkipSeed to skip training, -NoBuild to reuse the app image
```
Steps:
1. Checks that Docker is running and `.venv` exists.
2. Starts `fake-gcs`, `mlflow` and `registry`, then waits for `http://localhost:5000/health`.
3. Seeds the model registry if `IrisClassifier` is not registered: runs `mlcicd.training.train`, `mlcicd.training.evaluate` (the regression gate) and `mlcicd.registry.register` with `PROFILE=local`. The modules are called directly because `dvc repro` skips an unchanged `train` stage and would log no run to a fresh MLflow.
4. Builds and starts `app`, `prometheus` and `grafana`, then waits for `http://localhost:8000/health`.

Result:

| Service | URL |
|---|---|
| API docs | http://localhost:8000/docs |
| MLflow | http://localhost:5000 |
| Prometheus targets | http://localhost:9090/targets |
| Grafana (admin / admin) | http://localhost:3000 |
| Streamlit page | `.\.venv-ui\Scripts\streamlit run ui/streamlit_app.py` |

### local-down.ps1
```powershell
.\scripts\local-down.ps1            # -Volumes also removes fake-gcs and registry volumes
```
Runs `docker compose down`. The compose MLflow keeps its SQLite file inside the container, so the registry is lost on every `down`; the next `local-up.ps1` re-seeds the model automatically.

---

## 2. Remote Environment (GCP)

Creates and removes the cloud setup with Terraform (`infra/gcp`): GCS bucket (DVC remote), Artifact Registry, Cloud Run service, runtime and deployer service accounts, Workload Identity Federation, and a Secret Manager secret for the DagsHub token. Both scripts ask for confirmation before changing anything.

### Pre-requisites
- One-time GCP setup (already done for your project): project with billing and a budget alert, and the APIs `run`, `artifactregistry`, `iam`, `iamcredentials`, `sts`, `cloudresourcemanager`, `storage` enabled.
- Tools on PATH: `gcloud`, `terraform`, `gh` (GitHub CLI), and `dvc` (activate `.venv` first).
- Logged in:
  ```powershell
  gcloud auth login
  gcloud config set project <your-project-id>
  gcloud auth application-default login
  gcloud auth application-default set-quota-project <your-project-id>
  gh auth login
  ```
- A local, git-ignored `.env` file in the repo root with the folder where Terraform state backups are copied (any folder outside the repo; see `.env.example`):
  ```
  GCP_BACKUP_DIR=<folder path>
  ```
  The script also accepts `$env:GCP_BACKUP_DIR`. If neither is set, it stops before doing anything.
- A DagsHub access token (the script asks for it once, masked, only when it is needed).
- Repo files are committed and pushed (workflows, `.dvc/config`, Terraform files), because CI uses the committed copies.

### gcp-up.ps1
```powershell
.\scripts\gcp-up.ps1                # -Yes skips prompts, -SkipData skips dvc push, -NoTrigger skips starting train
```
Steps:
1. Pre-flight: tools, active gcloud project, Application Default Credentials, `gh` login, backup setting.
2. `terraform init`.
3. Phase 1: creates only the Secret Manager API, the secret and its IAM (plan, confirm, apply). Cloud Run cannot start a revision that references a secret without a version, so the secret comes first.
4. Adds the DagsHub token as a secret version (masked prompt, written without a trailing newline) if no enabled version exists.
5. Phase 2: plans and applies everything else (confirm first), then copies `terraform.tfstate` to the backup folder with a timestamp.
6. Sets GitHub repo variables `WIF_PROVIDER`, `DEPLOYER_SA`, `GCP_PROJECT`, `GCP_REGION`, `DAGSHUB_USER` from the Terraform outputs, and the `DAGSHUB_TOKEN` secret if it is missing.
7. Ensures the DVC remote `gcs` points at the new bucket (written to `.dvc/config.local`, not committed) and runs `dvc push -r gcs`.
8. Writes `monitoring/prometheus.prod.yml` (git-ignored) with the new Cloud Run host as a prod scrape target.
9. Enables the `train` and `register-deploy` workflows and starts `train`; `register-deploy` follows automatically when it succeeds.

The Cloud Run URL shows Google's placeholder page until `register-deploy` finishes. Check progress with `gh run list`. To scrape prod locally:
```powershell
$env:PROM_CONFIG='../monitoring/prometheus.prod.yml'
docker compose -f infra/docker-compose.yml up prometheus grafana
```

### gcp-destroy.ps1
```powershell
.\scripts\gcp-destroy.ps1
```
Steps:
1. Pre-flight checks. Exits with "nothing to destroy" if the Terraform state is empty.
2. Copies `terraform.tfstate` to the backup folder.
3. Sets `force_destroy=true` on the DVC bucket with a targeted apply (a state-only change), so the bucket can be deleted with its contents.
4. Shows the destroy plan and requires you to type the project id.
5. Destroys everything and checks that the state is empty, then lists Cloud Run, buckets, Artifact Registry and secrets (read-only) so you can see nothing is left.
6. Removes `monitoring/prometheus.prod.yml` and the stale GitHub variables `WIF_PROVIDER` and `DEPLOYER_SA`.

What survives: the GCP project itself (no cost with no resources), the DagsHub account and registry, the `gcs` remote entry in `.dvc/config`, and your local data. The Terraform state backups stay in the backup folder.

### Notes
- A new random 4-character suffix is generated for the Workload Identity pool and provider IDs after each destroy, because deleted IDs stay reserved for about 30 days.
- `train` and `register-deploy` are manual, so a push to `main` only runs `CI`. Start `train` from the Actions tab or through `gcp-up.ps1`.
- A failed `register-deploy` usually hides an app start-up error. Read it with `gcloud run services logs read churn-app --region asia-south1 --limit 30`.
