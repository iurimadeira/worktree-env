from .errors import PortsExhaustedError


def allocate_ports(
    port_names: list[str],
    already_allocated: set[int],
    port_range: tuple[int, int],
) -> dict[str, int]:
    used = set(already_allocated)
    result = {}

    range_start, range_end = port_range

    for name in port_names:
        port = _next_available(range_start, range_end, used)
        result[name] = port
        used.add(port)

    return result


def _next_available(start: int, end: int, used: set[int]) -> int:
    for port in range(start, end + 1):
        if port not in used:
            return port
    raise PortsExhaustedError(
        f"No available ports in range {start}-{end}. "
        "Run 'worktree-env gc' to prune stale entries or expand the range "
        "in ~/.config/worktree-env/config.toml"
    )
