import os
from pathlib import Path

from dotenv import load_dotenv

PROFILE = os.getenv("PROFILE", "local")

REPO_ROOT = Path(__file__).resolve().parents[2]
env_path = REPO_ROOT / "profiles" / f"{PROFILE}.env"

if not env_path.exists():
    raise FileNotFoundError(f"Profile env file not found: {env_path}")

load_dotenv(dotenv_path=env_path)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
DVC_REMOTE_URL = os.getenv("DVC_REMOTE_URL")
DVC_REMOTE_ENDPOINT = os.getenv("DVC_REMOTE_ENDPOINT")
REGISTRY_URL = os.getenv("REGISTRY_URL")
APP_URL = os.getenv("APP_URL")
