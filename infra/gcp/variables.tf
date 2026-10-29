variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "asia-south1"
}

variable "github_repo" {
  type    = string
  default = "Raxit-AI-Portfolio/mlops-batch-pipeline"
}

variable "github_branch_ref" {
  type    = string
  default = "refs/heads/main"
}

variable "app_name" {
  type    = string
  default = "churn-app"
}

variable "dagshub_user" {
  type    = string
  default = "raxitsoni-ai"
}

variable "force_destroy" {
  type    = bool
  default = false
}

variable "allow_unauthenticated" {
  type    = bool
  default = true
}