from os import environ

from buildbot.steps.shell import ShellCommand

# store 'secret' environment variables in a separate dictionary
SECRETS = {}


def filter_secrets():
    for key in dict(environ):
        if key.startswith('SECRET_'):
            SECRETS[key.lstrip('SECRET_')] = environ.pop(key)


class ShellCommandWithSecrets(ShellCommand):
    """ Execute a shell command that needs secret environment variables.

    All variables on the form SECRET_{var} will be passed as {var} inside the
    worker. Naturally, the environment is not logged during such a step.

    """

    def __init__(self, *args, **kwargs):
        new_env = kwargs.pop('env', {})
        new_env.update(SECRETS)

        kwargs.update({
            'logEnviron': False,
            'env': new_env,
        })

        super(ShellCommandWithSecrets, self).__init__(*args, **kwargs)
