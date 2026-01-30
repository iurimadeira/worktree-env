from worktree_env.template import build_template_vars, render_env, render_template


class TestBuildTemplateVars:
    def test_includes_project_and_worktree(self):
        result = build_template_vars("myapp", "main", {})
        assert result == {"project": "myapp", "worktree": "main"}

    def test_includes_ports(self):
        result = build_template_vars("myapp", "main", {"PORT": 4000})
        assert result["port.PORT"] == "4000"


class TestRenderTemplate:
    def test_simple_replacement(self):
        assert render_template("{project}_dev", {"project": "myapp"}) == "myapp_dev"

    def test_dotted_key(self):
        result = render_template(
            "http://localhost:{port.PORT}",
            {"port.PORT": "4000"},
        )
        assert result == "http://localhost:4000"

    def test_unknown_key_kept(self):
        assert render_template("{unknown}", {}) == "{unknown}"

    def test_multiple_replacements(self):
        result = render_template(
            "{project}_{worktree}",
            {"project": "app", "worktree": "feat"},
        )
        assert result == "app_feat"


class TestRenderEnv:
    def test_renders_env_specs(self):
        specs = {
            "DB_NAME": {"template": "{project}_dev_{worktree}"},
            "URL": {"template": "http://localhost:{port.PORT}"},
        }
        variables = {
            "project": "myapp",
            "worktree": "main",
            "port.PORT": "4000",
        }
        result = render_env(specs, variables)
        assert result == {
            "DB_NAME": "myapp_dev_main",
            "URL": "http://localhost:4000",
        }

    def test_empty_template(self):
        result = render_env({"X": {}}, {"project": "a"})
        assert result == {"X": ""}
