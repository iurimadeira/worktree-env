import pytest

from worktree_env.config import (
    GlobalConfig,
    ProjectConfig,
    config_dir,
    load_global_config,
    load_project_config,
)
from worktree_env.errors import ConfigNotFoundError


class TestLoadProjectConfig:
    def test_loads_valid_config(self, tmp_path):
        toml = tmp_path / ".worktree-env.toml"
        toml.write_text(
            '[project]\nname = "myapp"\n\n'
            "[ports]\nPORT = {}\n\n"
            "[env]\n"
            'DB_NAME = { template = "{project}_dev_{worktree}" }\n'
        )
        config = load_project_config(tmp_path)
        assert config.name == "myapp"
        assert "PORT" in config.ports
        assert "DB_NAME" in config.env

    def test_raises_when_no_file(self, tmp_path):
        with pytest.raises(ConfigNotFoundError):
            load_project_config(tmp_path)

    def test_raises_when_no_name(self, tmp_path):
        toml = tmp_path / ".worktree-env.toml"
        toml.write_text("[project]\n")
        with pytest.raises(ConfigNotFoundError, match="must have"):
            load_project_config(tmp_path)


class TestLoadGlobalConfig:
    def test_returns_defaults_when_no_file(self, registry_dir):
        config = load_global_config()
        assert config.port_range == (4000, 8999)

    def test_loads_custom_range(self, registry_dir):
        config_file = registry_dir / "config.toml"
        config_file.write_text("[ports]\nrange = [5000, 5999]\n")
        config = load_global_config()
        assert config.port_range == (5000, 5999)


class TestConfigDir:
    def test_respects_env_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("WORKTREE_ENV_CONFIG_DIR", str(tmp_path))
        assert config_dir() == tmp_path
