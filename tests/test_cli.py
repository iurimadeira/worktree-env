import os

from click.testing import CliRunner

from worktree_env.cli import main


class TestInitCommand:
    def test_init_creates_envrc(self, git_worktree, registry_dir):
        toml = git_worktree / ".worktree-env.toml"
        toml.write_text(
            '[project]\nname = "testapp"\n\n'
            "[ports]\nPORT = {}\n\n"
            "[env]\n"
            'DB_NAME = { template = "{project}_dev_{worktree}" }\n'
        )

        runner = CliRunner()
        result = runner.invoke(main, ["init"], env={
            "WORKTREE_ENV_CONFIG_DIR": str(registry_dir),
            "GIT_DIR": str(git_worktree / ".git"),
        }, catch_exceptions=False)

        os.chdir(git_worktree)
        result = runner.invoke(main, ["init"], env={
            "WORKTREE_ENV_CONFIG_DIR": str(registry_dir),
        }, catch_exceptions=False)

        assert result.exit_code == 0
        assert "testapp" in result.output

        envrc = git_worktree / ".envrc"
        assert envrc.exists()
        content = envrc.read_text()
        assert "export PORT=" in content
        assert "export DB_NAME=" in content

    def test_init_idempotent(self, git_worktree, registry_dir):
        toml = git_worktree / ".worktree-env.toml"
        toml.write_text(
            '[project]\nname = "testapp"\n\n'
            "[ports]\nPORT = {}\n"
        )

        runner = CliRunner()
        os.chdir(git_worktree)
        env = {"WORKTREE_ENV_CONFIG_DIR": str(registry_dir)}

        result1 = runner.invoke(main, ["init"], env=env, catch_exceptions=False)
        assert result1.exit_code == 0

        # Extract port from first run
        for line in result1.output.splitlines():
            if "PORT=" in line and "Envrc" not in line:
                port1 = line.strip().split("=")[-1]
                break

        result2 = runner.invoke(main, ["init"], env=env, catch_exceptions=False)
        assert result2.exit_code == 0

        for line in result2.output.splitlines():
            if "PORT=" in line and "Envrc" not in line:
                port2 = line.strip().split("=")[-1]
                break

        assert port1 == port2


class TestShowCommand:
    def test_show_after_init(self, git_worktree, registry_dir):
        toml = git_worktree / ".worktree-env.toml"
        toml.write_text(
            '[project]\nname = "testapp"\n\n'
            "[ports]\nPORT = {}\n\n"
            "[env]\n"
            'DB_NAME = { template = "{project}_dev_{worktree}" }\n'
        )

        runner = CliRunner()
        os.chdir(git_worktree)
        env = {"WORKTREE_ENV_CONFIG_DIR": str(registry_dir)}

        runner.invoke(main, ["init"], env=env, catch_exceptions=False)
        result = runner.invoke(main, ["show"], env=env, catch_exceptions=False)

        assert result.exit_code == 0
        assert "PORT=" in result.output
        assert "DB_NAME=" in result.output

    def test_show_without_init(self, git_worktree, registry_dir):
        toml = git_worktree / ".worktree-env.toml"
        toml.write_text('[project]\nname = "testapp"\n')

        runner = CliRunner()
        os.chdir(git_worktree)
        env = {"WORKTREE_ENV_CONFIG_DIR": str(registry_dir)}

        result = runner.invoke(main, ["show"], env=env)
        assert result.exit_code != 0
        assert "No allocation found" in result.output


class TestReleaseCommand:
    def test_release_after_init(self, git_worktree, registry_dir):
        toml = git_worktree / ".worktree-env.toml"
        toml.write_text(
            '[project]\nname = "testapp"\n\n'
            "[ports]\nPORT = {}\n"
        )

        runner = CliRunner()
        os.chdir(git_worktree)
        env = {"WORKTREE_ENV_CONFIG_DIR": str(registry_dir)}

        runner.invoke(main, ["init"], env=env, catch_exceptions=False)
        assert (git_worktree / ".envrc").exists()

        result = runner.invoke(main, ["release"], env=env, catch_exceptions=False)
        assert result.exit_code == 0
        assert "released" in result.output.lower()
        assert not (git_worktree / ".envrc").exists()


class TestStatusCommand:
    def test_status_shows_worktrees(self, git_worktree, registry_dir):
        toml = git_worktree / ".worktree-env.toml"
        toml.write_text(
            '[project]\nname = "testapp"\n\n'
            "[ports]\nPORT = {}\n"
        )

        runner = CliRunner()
        os.chdir(git_worktree)
        env = {"WORKTREE_ENV_CONFIG_DIR": str(registry_dir)}

        runner.invoke(main, ["init"], env=env, catch_exceptions=False)
        result = runner.invoke(main, ["status"], env=env, catch_exceptions=False)

        assert result.exit_code == 0
        assert "testapp" in result.output


class TestGcCommand:
    def test_gc_no_stale(self, registry_dir):
        runner = CliRunner()
        env = {"WORKTREE_ENV_CONFIG_DIR": str(registry_dir)}
        result = runner.invoke(main, ["gc"], env=env, catch_exceptions=False)
        assert result.exit_code == 0
        assert "No stale entries" in result.output
