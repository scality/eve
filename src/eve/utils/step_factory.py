from os import environ

from buildbot.process.properties import Interpolate
from buildbot.steps.http import HTTPStep
from buildbot.steps.source.git import Git
from buildbot.plugins import steps
from requests.auth import HTTPBasicAuth
from ..steps.shell_command_with_secrets import ShellCommandWithSecrets  # noqa: F401, pylint: disable=relative-import,unused-import


def step_factory(custom_steps, step_type, **params):
    """Generate a buildbot step from dictionnary."""
    try:
        # try to see if the required step is imported or
        # defined in the custom steps
        _cls = custom_steps[step_type]
    except KeyError:
        # otherwise try in local context
        try:
            # try in local context
            _cls = globals()[step_type]
        except KeyError:
            # otherwise import the step from standars buildbot steps
            try:
                _cls = getattr(steps, step_type)
            except AttributeError:
                raise Exception('Could not load step %s' % step_type)

    # Replace the %(prop:*)s in the text with an Interpolate obj
    params = replace_with_interpolate(params)

    if issubclass(_cls, Git):
        # retry 10 times if git step fails, wait 60s between retries
        params['retry'] = (60, 10)

    # hack to avoid putting clear passwords into the YAML file
    # for the HTTP step
    if issubclass(_cls, HTTPStep):
        pwd = params['auth'][1].replace('$', '')
        if pwd in environ:
            params['auth'] = HTTPBasicAuth(
                params['auth'][0], environ[pwd])

    # Hack! Buildbot does not accept unicode step names
    if 'name' in params and isinstance(params['name'], unicode):
        params['name'] = params['name'].encode('utf-8')

    return _cls(**params)


def replace_with_interpolate(obj):
    """Interpolate nested %(prop:obj)s in step arguments.

    Read step arguments from the yaml file and replaces them with
    interpolate objects when relevant so they can be replaced with
    properties when run.
    """

    if isinstance(obj, dict):
        return {k: replace_with_interpolate(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_with_interpolate(elem) for elem in obj]
    elif isinstance(obj, basestring) and 'prop:' in obj:
        return Interpolate(obj)
    else:
        return obj
