import re


def build_template_vars(
    project_name: str,
    worktree_name: str,
    ports: dict[str, int],
) -> dict[str, str]:
    variables = {
        "project": project_name,
        "worktree": worktree_name,
    }
    for port_name, port_value in ports.items():
        variables[f"port.{port_name}"] = str(port_value)
    return variables


def render_template(template_str: str, variables: dict[str, str]) -> str:
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key in variables:
            return variables[key]
        return match.group(0)

    return re.sub(r"\{([^}]+)\}", replacer, template_str)


def render_env(
    env_specs: dict[str, dict],
    template_vars: dict[str, str],
) -> dict[str, str]:
    result = {}
    for var_name, spec in env_specs.items():
        template = spec.get("template", "")
        result[var_name] = render_template(template, template_vars)
    return result
