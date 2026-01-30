import fcntl
import json
from contextlib import contextmanager
from pathlib import Path

from .config import config_dir
from .errors import RegistryCorruptedError


def _registry_path() -> Path:
    return config_dir() / "registry.json"


def _lock_path() -> Path:
    return config_dir() / "registry.lock"


def _empty_registry() -> dict:
    return {"projects": {}}


@contextmanager
def locked_registry():
    dir_path = config_dir()
    dir_path.mkdir(parents=True, exist_ok=True)

    lock_path = _lock_path()
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX)

        reg_path = _registry_path()
        if reg_path.exists():
            try:
                data = json.loads(reg_path.read_text())
            except (json.JSONDecodeError, ValueError) as e:
                raise RegistryCorruptedError(
                    f"Registry file is corrupted: {e}. "
                    f"Back up and delete {reg_path} to reset."
                )
        else:
            data = _empty_registry()

        yield data

        reg_path.write_text(json.dumps(data, indent=2) + "\n")
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()


def get_allocation(
    data: dict, project: str, path: str
) -> dict | None:
    projects = data.get("projects", {})
    project_data = projects.get(project, {})
    return project_data.get(path)


def set_allocation(
    data: dict,
    project: str,
    path: str,
    allocation: dict,
) -> None:
    projects = data.setdefault("projects", {})
    project_entries = projects.setdefault(project, {})
    project_entries[path] = allocation


def remove_allocation(data: dict, project: str, path: str) -> bool:
    projects = data.get("projects", {})
    project_data = projects.get(project, {})
    if path in project_data:
        del project_data[path]
        if not project_data:
            del projects[project]
        return True
    return False


def get_all_allocated_ports(data: dict) -> set[int]:
    ports = set()
    for project_entries in data.get("projects", {}).values():
        for allocation in project_entries.values():
            for port in allocation.get("ports", {}).values():
                ports.add(port)
    return ports


def gc_stale_entries(data: dict) -> list[str]:
    removed = []
    projects = data.get("projects", {})
    for project_name in list(projects.keys()):
        entries = projects[project_name]
        for path in list(entries.keys()):
            if not Path(path).exists():
                del entries[path]
                removed.append(f"{project_name}: {path}")
        if not entries:
            del projects[project_name]
    return removed
