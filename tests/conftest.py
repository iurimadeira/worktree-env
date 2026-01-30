import subprocess

import pytest

from worktree_env.config import ProjectConfig


@pytest.fixture
def sample_project_config():
    return ProjectConfig(
        name="myapp",
        ports={"PORT": {}, "LIVE_PORT": {}},
        env={
            "DB_NAME": {"template": "{project}_dev_{worktree}"},
            "TEST_DB_NAME": {"template": "{project}_test_{worktree}"},
        },
    )


@pytest.fixture
def registry_dir(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    monkeypatch.setenv("WORKTREE_ENV_CONFIG_DIR", str(config_dir))
    return config_dir


@pytest.fixture
def git_worktree(tmp_path):
    repo = tmp_path / "my-repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init"], cwd=repo, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    return repo
