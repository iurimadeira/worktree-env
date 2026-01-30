from pathlib import Path

import pytest

from worktree_env.errors import NotAGitRepoError
from worktree_env.worktree import get_repo_root, get_worktree_name, sanitize_name


class TestGetRepoRoot:
    def test_returns_root_for_git_repo(self, git_worktree):
        root = get_repo_root(git_worktree)
        assert root == git_worktree

    def test_raises_for_non_git_dir(self, tmp_path):
        with pytest.raises(NotAGitRepoError):
            get_repo_root(tmp_path)


class TestGetWorktreeName:
    def test_returns_basename(self):
        assert get_worktree_name(Path("/home/user/workspace/my-repo")) == "my-repo"

    def test_handles_nested_path(self):
        assert get_worktree_name(Path("/a/b/c")) == "c"


class TestSanitizeName:
    def test_lowercase(self):
        assert sanitize_name("MyRepo") == "myrepo"

    def test_replaces_non_alnum(self):
        assert sanitize_name("my-repo.v2") == "my_repo_v2"

    def test_collapses_underscores(self):
        assert sanitize_name("my--repo__v2") == "my_repo_v2"

    def test_strips_edge_underscores(self):
        assert sanitize_name("-my-repo-") == "my_repo"

    def test_complex_name(self):
        assert sanitize_name("DEV-38/feature_branch!") == "dev_38_feature_branch"
