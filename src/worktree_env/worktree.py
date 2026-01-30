import re
import subprocess
from pathlib import Path

from .errors import NotAGitRepoError


def get_repo_root(path: Path | None = None) -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            cwd=path or Path.cwd(),
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        raise NotAGitRepoError(
            f"Not a git repository: {path or Path.cwd()}"
        )


def get_worktree_name(path: Path) -> str:
    return path.name


def sanitize_name(name: str) -> str:
    lowered = name.lower()
    replaced = re.sub(r"[^a-z0-9]", "_", lowered)
    collapsed = re.sub(r"_+", "_", replaced)
    return collapsed.strip("_")
