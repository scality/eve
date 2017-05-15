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
"""Hack to allow build step name interpolation."""

from functools import wraps

from buildbot.process.buildstep import BuildStep
from buildbot.process.properties import Interpolate
from twisted.internet import defer


def hide_interpolatable_name(func):
    """Hide the interpolatable name to be later rendered."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self._interpolatable_name = kwargs.pop('name', None) or self.name
        self.name = str(self._interpolatable_name)
        return func(self, *args, **kwargs)

    return wrapper


def render_interpolatable_name(func):
    """Render the hidden interpolatable name before proceeding."""

    @wraps(func)
    @defer.inlineCallbacks
    def wrapper(self, *args, **kwargs):
        if isinstance(self._interpolatable_name, Interpolate):
            finished = self.build.render(self._interpolatable_name)

            def set_name(res):
                self.name = res

            finished.addCallback(set_name)
            yield finished
        res = yield func(self, *args, **kwargs)
        defer.returnValue(res)

    return wrapper


def patch():
    BuildStep.__init__ = hide_interpolatable_name(BuildStep.__init__)
    BuildStep.startStep = render_interpolatable_name(BuildStep.startStep)
