
resource "google_storage_bucket" "dvc" {
  name                        = "${var.project_id}-dvc"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.force_destroy
  versioning { enabled = true }
}

resource "google_artifact_registry_repository" "images" {
  repository_id = "mlops"
  location      = var.region
  format        = "DOCKER"
}

resource "google_service_account" "runtime" {
  account_id   = "${var.app_name}-runtime"
  display_name = "Cloud Run runtime"
}

resource "google_storage_bucket_iam_member" "runtime_read" {
  bucket = google_storage_bucket.dvc.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_cloud_run_v2_service" "app" {
  name                = var.app_name
  location            = var.region
  deletion_protection = false

  template {
    service_account = google_service_account.runtime.email
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      env {
        name  = "PROFILE"
        value = "prod"
      }
      env {
        name  = "MLFLOW_TRACKING_USERNAME"
        value = var.dagshub_user
      }
      env {
        name = "MLFLOW_TRACKING_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.dagshub_token.secret_id
            version = "latest"
          }
        }
      }
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
  }

  depends_on = [google_secret_manager_secret_iam_member.runtime_access]

  lifecycle {
    ignore_changes = [template[0].containers[0].image, template[0].labels, scaling, client, client_version]
  }
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.allow_unauthenticated ? 1 : 0
  name     = google_cloud_run_v2_service.app.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

