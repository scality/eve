from buildbot.plugins import util
from buildbot.steps.shell import ShellCommand


class ShellCommandWithSecrets(ShellCommand):
    """Execute a shell command that needs secret environment variables.

    All variables on the form SECRET_{var} will be passed as {var} inside the
    worker. Naturally, the environment is not logged during such a step.

    """

    def __init__(self, *args, **kwargs):
        new_env = kwargs.pop('env', {})
        new_env.update(util.get_secrets())

        kwargs.update({
            'logEnviron': False,
            'env': new_env,
        })

        super(ShellCommandWithSecrets, self).__init__(*args, **kwargs)
