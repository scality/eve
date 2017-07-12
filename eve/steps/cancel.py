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

from buildbot.plugins import util
from buildbot.process.properties import Interpolate
from buildbot.process.results import CANCELLED
from buildbot.steps.shell import ShellCommand


class CancelCommand(ShellCommand):
    """Cancel a build according to result of command."""

    name = 'CancelCommand'

    def commandComplete(self, cmd):
        if cmd.didFail():
            self.finished(CANCELLED)
            return

        return super(CancelCommand, self).commandComplete(cmd)


class CancelNonTipBuild(CancelCommand):
    """Cancel if the current revision is not the tip of the branch."""

    name = 'CancelNonTipBuild'

    def __init__(self, **kwargs):
        super(CancelNonTipBuild, self).__init__(
            command=Interpolate(
                '[ "%(prop:revision)s" = "" ] '
                '|| [ "$(git ls-remote origin refs/heads/%(prop:branch)s'
                ' | cut -f1)" = '
                '"%(prop:revision)s" ]'),
            descriptionDone='CancelNonTipBuild',
            hideStepIf=util.hideStepIfSuccess,
            **kwargs)


class CancelOldBuild(CancelCommand):
    """Cancel if the build is previous buildbot instance."""

    name = 'CancelOldBuild'

    def __init__(self, **kwargs):
        # pylint: disable=anomalous-backslash-in-string
        super(CancelOldBuild, self).__init__(
            hideStepIf=util.hideStepIfSuccess,
            command=Interpolate(
                '[ $(expr "{}" \< "%(prop:start_time)s") -eq 1 ]'.format(
                    util.env.MASTER_START_TIME)),
            **kwargs)
