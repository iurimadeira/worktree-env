# worktree-env

Isolated ports, database names, and environment variables for each Git worktree.

When working with multiple Git worktrees of the same repository, you often run into port conflicts and database name collisions. **worktree-env** automatically allocates unique ports and generates per-worktree environment variables, writing them to a `.envrc` file for seamless [direnv](https://direnv.net/) integration.

## Installation

```bash
pip install git+https://github.com/iurimadeira/worktree-env.git
```

Requires Python 3.10+.

## Quick Start

1. Create a `.worktree-env.toml` in your repository root:

```toml
[project]
name = "myapp"

[ports]
PORT = {}
LIVE_PORT = {}

[env]
DATABASE_URL = { template = "postgres://localhost:5432/{project}_dev_{worktree}" }
API_URL = { template = "http://localhost:{port.PORT}" }
```

2. Initialize the worktree environment:

```bash
worktree-env init
```

This allocates unique ports, renders environment variables, writes a `.envrc` file, and runs `direnv allow` if direnv is installed.

## Commands

| Command | Description |
|---------|-------------|
| `worktree-env init` | Allocate ports and generate `.envrc` for the current worktree |
| `worktree-env show` | Display allocated ports and environment variables |
| `worktree-env status` | List all registered worktrees for the project |
| `worktree-env release` | Remove the current worktree's allocation and `.envrc` |
| `worktree-env gc` | Remove stale registry entries for deleted worktree paths |

## Configuration

### Project config (`.worktree-env.toml`)

Placed at the root of your Git repository.

```toml
[project]
name = "myapp"    # Required. Identifies the project in the shared registry.

[ports]
PORT = {}         # Each key becomes an environment variable with an allocated port.
LIVE_PORT = {}

[env]
# Templates can reference {project}, {worktree}, and {port.<NAME>}.
DB_NAME = { template = "{project}_dev_{worktree}" }
API_URL = { template = "http://localhost:{port.PORT}/api" }
```

### Global config (`~/.config/worktree-env/config.toml`)

Optional. Overrides defaults.

```toml
[global]
port_range = [4000, 8999]   # Range of ports available for allocation (default)
```

The config directory can be overridden with the `WORKTREE_ENV_CONFIG_DIR` environment variable.

## How It Works

- A shared **registry** (`~/.config/worktree-env/registry.json`) tracks port allocations across all projects and worktrees.
- File-level locking prevents conflicts when multiple worktrees initialize concurrently.
- Running `init` is **idempotent** -- existing port allocations are reused, and only newly added port names get fresh allocations.
- **Garbage collection** runs automatically during `init`, removing entries for worktree paths that no longer exist on disk.
- Worktree names are derived from the directory basename and sanitized (lowercased, non-alphanumeric characters replaced with underscores).

## Template Variables

Templates in the `[env]` section support these variables:

| Variable | Value |
|----------|-------|
| `{project}` | Project name from config |
| `{worktree}` | Sanitized worktree directory name |
| `{port.<NAME>}` | Allocated port for the given port name |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

See [LICENSE](LICENSE) for details.
