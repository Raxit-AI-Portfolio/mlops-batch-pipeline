import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def dvc_config():
    with open(REPO_ROOT / "dvc.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def params_config():
    with open(REPO_ROOT / "params.yaml") as f:
        return yaml.safe_load(f)


@pytest.mark.infra
def test_dvc_yaml_has_expected_stages(dvc_config):
    assert set(dvc_config["stages"].keys()) == {"validate", "train", "evaluate"}


def _stage_produced_paths(dvc_config):
    produced = set()
    for stage in dvc_config["stages"].values():
        for section in ("outs", "metrics", "plots"):
            for entry in stage.get(section, []):
                produced.add(next(iter(entry)) if isinstance(entry, dict) else entry)
    return produced


@pytest.mark.infra
def test_every_dvc_stage_dep_is_accounted_for(dvc_config):
    """Checks wiring, not data presence: CI runs neither `dvc pull` nor `dvc repro`,
    so a dep is legitimately absent if it is DVC-tracked or produced by another stage.
    """
    produced = _stage_produced_paths(dvc_config)

    for stage_name, stage in dvc_config["stages"].items():
        for dep in stage.get("deps", []):
            dep_path = REPO_ROOT / dep
            tracked = dep_path.with_suffix(dep_path.suffix + ".dvc").exists()
            assert dep_path.exists() or tracked or dep in produced, (
                f"stage {stage_name} dep is unwired: {dep} "
                "(not on disk, not DVC-tracked, not produced by another stage)"
            )


@pytest.mark.infra
def test_dvc_dag_is_acyclic():
    dvc_bin = shutil.which("dvc")
    if not dvc_bin:
        pytest.skip("dvc executable not on PATH")
    result = subprocess.run(
        [dvc_bin, "dag"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.infra
def test_params_yaml_has_keys_referenced_by_dvc_yaml(dvc_config, params_config):
    for stage in dvc_config["stages"].values():
        for param_ref in stage.get("params", []):
            section, key = param_ref.split(".")
            assert section in params_config, f"missing params section: {section}"
            assert key in params_config[section], f"missing param key: {param_ref}"


@pytest.mark.infra
def test_every_dvc_file_is_collected_into_dvc_index():
    """Guards a silent-data-loss mode: a blanket .gitignore pattern such as
    `/data/raw/*` makes scmrepo report the directory itself as ignored, DVC
    prunes ignored directories from its stage walk, and push/pull/checkout then
    no-op on every .dvc file inside it without any error.
    """
    from dvc.repo import Repo

    on_disk = {
        p.resolve()
        for p in REPO_ROOT.rglob("*.dvc")
        if ".venv" not in p.parts and ".dvc" not in p.parts
    }
    repo = Repo(str(REPO_ROOT))
    collected = {Path(s.path).resolve() for s in repo.index.stages if str(s.path).endswith(".dvc")}

    missing = on_disk - collected
    assert not missing, f".dvc files ignored by DVC's stage walk: {sorted(missing)}"


@pytest.mark.infra
def test_gs_remote_does_not_rely_on_s3_only_endpointurl():
    """`endpointurl` is an S3 remote option; the gs remote silently ignores it,
    so DVC would hit real storage.googleapis.com. fake-gcs redirection must come
    from STORAGE_EMULATOR_HOST, which gcsfs reads.
    """
    config = (REPO_ROOT / ".dvc" / "config").read_text()
    assert "endpointurl" not in config, ".dvc/config sets endpointurl on a gs remote"

    for profile in ("local", "github"):
        env_text = (REPO_ROOT / "profiles" / f"{profile}.env").read_text()
        assert (
            "STORAGE_EMULATOR_HOST" in env_text
        ), f"profiles/{profile}.env must set STORAGE_EMULATOR_HOST for fake-gcs"


@pytest.mark.infra
@pytest.mark.parametrize("profile", ["local", "github", "prod"])
def test_profile_env_loads_without_error(profile):
    env_path = REPO_ROOT / "profiles" / f"{profile}.env"
    assert env_path.exists(), f"missing profile: {env_path}"

    loaded = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert "=" in line, f"malformed line in {env_path}: {line!r}"
        key, _, value = line.partition("=")
        loaded[key.strip()] = value.strip()

    for required_key in ("PROFILE", "MLFLOW_TRACKING_URI"):
        assert required_key in loaded, f"{env_path} missing {required_key}"
