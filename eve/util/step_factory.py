# Copyright 2017 Scality
#
# This file is part of Eve.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.

from distutils.util import strtobool
from os import environ
import re

from buildbot.plugins import steps, util
from buildbot.process.properties import Interpolate
from buildbot.steps.http import HTTPStep
from buildbot.steps.source.git import Git
from requests.auth import HTTPBasicAuth


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

    # step names end up as keys in db and can't be too long
    if 'name' in params:
        stepname = params['name']
        # Take care of cutting interpolates properly.
        # This is an imperfect solution, as the interpolate
        # may resolve to a much longer string at build time.
        # (but the build would then fail)
        interpolates = list(re.finditer(r'%\(.*?(\)s)', stepname))
        for interp in reversed(interpolates):
            if interp.start() < 50 and interp.end() >= 50:
                stepname = stepname[:interp.start()]
                break
        params['name'] = stepname[:50]

    # Replace the %(prop:*)s in the text with an Interpolate obj
    params = util.replace_with_interpolate(params)

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

    return _cls(**params)


BOOLEAN_PROPERTIES = {'doStepIf', 'hideStepIf'}


def replace_with_interpolate(obj, key=None):
    """Interpolate nested %(prop:obj)s in step arguments.

    Read step arguments from the yaml file and replaces them with
    interpolate objects when relevant so they can be replaced with
    properties when run.

    """

    if isinstance(obj, dict):
        return {k: replace_with_interpolate(v, key=k) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_with_interpolate(elem) for elem in obj]
    elif isinstance(obj, str) and ('prop:' in obj or 'secret:' in obj):
        if key in BOOLEAN_PROPERTIES:
            return BooleanInterpolate(obj)
        return Interpolate(obj)
    else:
        return obj


class BooleanInterpolate(Interpolate):
    INTERPOLATION_REGEX = re.compile(r'^%\((prop|secret):[\w._-]*\)s$')

    def __init__(self, fmtstring):
        if not BooleanInterpolate.INTERPOLATION_REGEX.match(fmtstring):
            raise ValueError(
                "Invalid format to cast as a boolean: "
                "please only use '%(prop|secret:...)s'"
            )

        super(BooleanInterpolate, self).__init__(fmtstring)

    def getRenderingFor(self, build):
        d = super(BooleanInterpolate, self).getRenderingFor(build)

        @d.addCallback
        def cast_as_bool(value):
            def error_callable(*_):
                raise ValueError(
                    'Invalid value to cast as boolean: {}'.format(value)
                )

            try:
                return bool(strtobool(value))
            except ValueError:
                return error_callable

        return d
