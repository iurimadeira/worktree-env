import os
from dataclasses import dataclass, field
from pathlib import Path

from .errors import ConfigNotFoundError

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


@dataclass
class ProjectConfig:
    name: str
    ports: dict[str, dict] = field(default_factory=dict)
    env: dict[str, dict] = field(default_factory=dict)


@dataclass
class GlobalConfig:
    port_range: tuple[int, int] = (4000, 8999)


def config_dir() -> Path:
    override = os.environ.get("WORKTREE_ENV_CONFIG_DIR")
    if override:
        return Path(override)
    return Path.home() / ".config" / "worktree-env"


def load_project_config(repo_root: Path) -> ProjectConfig:
    config_path = repo_root / ".worktree-env.toml"
    if not config_path.exists():
        raise ConfigNotFoundError(
            f"No .worktree-env.toml found in {repo_root}"
        )
    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    name = project.get("name")
    if not name:
        raise ConfigNotFoundError(
            ".worktree-env.toml must have [project] name"
        )

    return ProjectConfig(
        name=name,
        ports=data.get("ports", {}),
        env=data.get("env", {}),
    )


def load_global_config() -> GlobalConfig:
    config_path = config_dir() / "config.toml"
    if not config_path.exists():
        return GlobalConfig()

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    ports = data.get("ports", {})
    port_range = ports.get("range", [4000, 8999])
    return GlobalConfig(port_range=tuple(port_range))
