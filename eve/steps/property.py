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
"""Steps used to set overridable properties."""

from buildbot.process.results import SKIPPED
from buildbot.steps.master import SetProperty
from buildbot.steps.shell import SetPropertyFromCommand
from twisted.internet import defer


class EvePropertyMixin:
    def run(self):
        try:
            source = self.getProperties().getPropertySource(self.property)
        except KeyError:
            source = None
        if source == 'Force Build Form':
            self.addCompleteLog('skipped',
                                'Property "%s" already set by user' %
                                self.property)
            return defer.succeed(SKIPPED)
        else:
            # Figure out next `run()` to call in the mro excluding all the
            # class leading to this one
            mro = self.__class__.mro()
            mro = mro[mro.index(EvePropertyMixin) + 1:]
            for cls in mro:
                if hasattr(cls, 'run'):
                    return cls.run(self)
            raise AttributeError("'%s' object has no attribute 'run'" %
                                 self.__class__)


class EveProperty(EvePropertyMixin, SetProperty):
    pass


class EvePropertyFromCommand(EvePropertyMixin, SetPropertyFromCommand):
    pass
