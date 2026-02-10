import click

from .config import load_global_config, load_project_config
from .envrc import ensure_direnv, run_direnv_allow, write_envrc
from .errors import WorktreeEnvError
from .ports import allocate_ports
from .registry import (
    gc_stale_entries,
    get_all_allocated_ports,
    get_allocation,
    locked_registry,
    remove_allocation,
    set_allocation,
)
from .template import build_template_vars, render_env
from .worktree import get_repo_root, get_worktree_name, sanitize_name


@click.group()
def main():
    """Isolated ports, database names, and env vars for each Git worktree."""
    pass


@main.command()
def init():
    """Initialize environment for the current worktree."""
    try:
        repo_root = get_repo_root()
        worktree_name = sanitize_name(get_worktree_name(repo_root))

        project_config = load_project_config(repo_root)
        global_config = load_global_config()

        with locked_registry() as data:
            removed = gc_stale_entries(data)
            if removed:
                click.echo(f"GC: pruned {len(removed)} stale entries")

            path_key = str(repo_root)
            existing = get_allocation(data, project_config.name, path_key)

            all_ports = get_all_allocated_ports(data)
            # Exclude our own ports from the "used" set so re-init can reuse them
            if existing:
                for p in existing.get("ports", {}).values():
                    all_ports.discard(p)

            requested_port_names = list(project_config.ports.keys())

            # Reconcile: keep existing ports for names that still exist
            reused_ports = {}
            new_port_names = []
            if existing:
                old_ports = existing.get("ports", {})
                for name in requested_port_names:
                    if name in old_ports:
                        reused_ports[name] = old_ports[name]
                        all_ports.add(old_ports[name])
                    else:
                        new_port_names.append(name)
            else:
                new_port_names = requested_port_names

            newly_allocated = allocate_ports(
                new_port_names, all_ports, global_config.port_range
            )

            ports = {**reused_ports, **newly_allocated}

            template_vars = build_template_vars(
                project_config.name, worktree_name, ports
            )
            env_vars = render_env(project_config.env, template_vars)

            allocation = {
                "worktree": worktree_name,
                "ports": ports,
                "env": env_vars,
            }
            set_allocation(data, project_config.name, path_key, allocation)

        envrc_path = write_envrc(repo_root, env_vars, ports)

        ensure_direnv()
        run_direnv_allow(repo_root)

        click.echo(f"Project:  {project_config.name}")
        click.echo(f"Worktree: {worktree_name}")
        click.echo(f"Envrc:    {envrc_path}")
        if ports:
            click.echo("Ports:")
            for name, port in sorted(ports.items()):
                click.echo(f"  {name}={port}")
        if env_vars:
            click.echo("Env:")
            for name, value in sorted(env_vars.items()):
                click.echo(f"  {name}={value}")

    except WorktreeEnvError as e:
        raise click.ClickException(str(e))


@main.command()
def show():
    """Show env vars for the current worktree."""
    try:
        repo_root = get_repo_root()
        project_config = load_project_config(repo_root)
        path_key = str(repo_root)

        with locked_registry() as data:
            allocation = get_allocation(data, project_config.name, path_key)

        if not allocation:
            raise click.ClickException(
                "No allocation found. Run 'worktree-env init' first."
            )

        ports = allocation.get("ports", {})
        env_vars = allocation.get("env", {})

        merged = {}
        for name, value in ports.items():
            merged[name] = str(value)
        merged.update(env_vars)

        for key, value in sorted(merged.items()):
            click.echo(f"{key}={value}")

    except WorktreeEnvError as e:
        raise click.ClickException(str(e))


@main.command()
def release():
    """Release allocation and delete .envrc for the current worktree."""
    try:
        repo_root = get_repo_root()
        project_config = load_project_config(repo_root)
        path_key = str(repo_root)

        with locked_registry() as data:
            removed = remove_allocation(
                data, project_config.name, path_key
            )

        if not removed:
            click.echo("No allocation found for this worktree.")
            return

        envrc_path = repo_root / ".envrc"
        if envrc_path.exists():
            envrc_path.unlink()
            click.echo(f"Deleted {envrc_path}")

        click.echo("Allocation released.")

    except WorktreeEnvError as e:
        raise click.ClickException(str(e))


@main.command()
def status():
    """Show all worktrees for the current project."""
    try:
        repo_root = get_repo_root()
        project_config = load_project_config(repo_root)

        with locked_registry() as data:
            projects = data.get("projects", {})
            entries = projects.get(project_config.name, {})

        if not entries:
            click.echo("No worktrees registered for this project.")
            return

        click.echo(f"Project: {project_config.name}")
        click.echo(f"{'Worktree':<20} {'Path':<50} {'Ports'}")
        click.echo("-" * 90)
        for path, alloc in sorted(entries.items()):
            wt = alloc.get("worktree", "?")
            ports_str = ", ".join(
                f"{k}={v}" for k, v in sorted(alloc.get("ports", {}).items())
            )
            click.echo(f"{wt:<20} {path:<50} {ports_str}")

    except WorktreeEnvError as e:
        raise click.ClickException(str(e))


@main.command()
def gc():
    """Prune stale registry entries (paths that no longer exist)."""
    with locked_registry() as data:
        removed = gc_stale_entries(data)

    if removed:
        click.echo(f"Removed {len(removed)} stale entries:")
        for entry in removed:
            click.echo(f"  {entry}")
    else:
        click.echo("No stale entries found.")
