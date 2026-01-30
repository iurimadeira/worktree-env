class WorktreeEnvError(Exception):
    pass


class ConfigNotFoundError(WorktreeEnvError):
    pass


class RegistryCorruptedError(WorktreeEnvError):
    pass


class PortsExhaustedError(WorktreeEnvError):
    pass


class NotAGitRepoError(WorktreeEnvError):
    pass
