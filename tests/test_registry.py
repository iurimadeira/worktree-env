import json

import pytest

from worktree_env.errors import RegistryCorruptedError
from worktree_env.registry import (
    gc_stale_entries,
    get_all_allocated_ports,
    get_allocation,
    locked_registry,
    remove_allocation,
    set_allocation,
)


class TestLockedRegistry:
    def test_creates_new_registry(self, registry_dir):
        with locked_registry() as data:
            assert data == {"projects": {}}

        reg = registry_dir / "registry.json"
        assert reg.exists()
        assert json.loads(reg.read_text()) == {"projects": {}}

    def test_reads_existing_registry(self, registry_dir):
        reg = registry_dir / "registry.json"
        reg.write_text(json.dumps({"projects": {"myapp": {}}}))

        with locked_registry() as data:
            assert "myapp" in data["projects"]

    def test_raises_on_corrupted_json(self, registry_dir):
        reg = registry_dir / "registry.json"
        reg.write_text("not json{{{")

        with pytest.raises(RegistryCorruptedError):
            with locked_registry() as data:
                pass

    def test_writes_back_changes(self, registry_dir):
        with locked_registry() as data:
            data["projects"]["test"] = {"path": {"worktree": "x"}}

        reg = registry_dir / "registry.json"
        saved = json.loads(reg.read_text())
        assert "test" in saved["projects"]


class TestAllocationCRUD:
    def test_set_and_get(self):
        data = {"projects": {}}
        alloc = {"worktree": "main", "ports": {"PORT": 4000}}
        set_allocation(data, "myapp", "/path/to/repo", alloc)
        assert get_allocation(data, "myapp", "/path/to/repo") == alloc

    def test_get_nonexistent(self):
        data = {"projects": {}}
        assert get_allocation(data, "myapp", "/nope") is None

    def test_remove(self):
        data = {"projects": {"myapp": {"/path": {"worktree": "main"}}}}
        assert remove_allocation(data, "myapp", "/path") is True
        assert get_allocation(data, "myapp", "/path") is None
        assert "myapp" not in data["projects"]

    def test_remove_nonexistent(self):
        data = {"projects": {}}
        assert remove_allocation(data, "myapp", "/nope") is False


class TestGetAllAllocatedPorts:
    def test_collects_all_ports(self):
        data = {
            "projects": {
                "app1": {
                    "/a": {"ports": {"PORT": 4000}},
                    "/b": {"ports": {"PORT": 4001, "LIVE": 4002}},
                },
                "app2": {
                    "/c": {"ports": {"PORT": 4010}},
                },
            }
        }
        assert get_all_allocated_ports(data) == {4000, 4001, 4002, 4010}

    def test_empty_registry(self):
        assert get_all_allocated_ports({"projects": {}}) == set()


class TestGcStaleEntries:
    def test_removes_nonexistent_paths(self, tmp_path):
        existing_path = str(tmp_path)
        data = {
            "projects": {
                "myapp": {
                    existing_path: {"worktree": "ok"},
                    "/nonexistent/path": {"worktree": "gone"},
                }
            }
        }
        removed = gc_stale_entries(data)
        assert len(removed) == 1
        assert "/nonexistent/path" in removed[0]
        assert existing_path in data["projects"]["myapp"]

    def test_removes_empty_project(self):
        data = {
            "projects": {
                "myapp": {
                    "/gone1": {"worktree": "a"},
                    "/gone2": {"worktree": "b"},
                }
            }
        }
        gc_stale_entries(data)
        assert "myapp" not in data["projects"]
