import pytest

from worktree_env.errors import PortsExhaustedError
from worktree_env.ports import allocate_ports


class TestAllocatePorts:
    def test_allocates_from_start(self):
        result = allocate_ports(["PORT"], set(), (4000, 4999))
        assert result == {"PORT": 4000}

    def test_skips_already_allocated(self):
        result = allocate_ports(["PORT"], {4000, 4001}, (4000, 4999))
        assert result == {"PORT": 4002}

    def test_allocates_multiple(self):
        result = allocate_ports(
            ["PORT", "LIVE_PORT"], set(), (4000, 4999)
        )
        assert result == {"PORT": 4000, "LIVE_PORT": 4001}

    def test_multiple_skip_used(self):
        result = allocate_ports(
            ["A", "B", "C"], {4000, 4002}, (4000, 4999)
        )
        assert result == {"A": 4001, "B": 4003, "C": 4004}

    def test_raises_when_exhausted(self):
        with pytest.raises(PortsExhaustedError):
            allocate_ports(["PORT"], {4000}, (4000, 4000))

    def test_empty_port_names(self):
        result = allocate_ports([], set(), (4000, 4999))
        assert result == {}
