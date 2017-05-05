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

from buildbot.locks import MasterLock
from buildbot.plugins import util
from buildbot.process import logobserver
from buildbot.process.results import SUCCESS
from buildbot.steps.master import MasterShellCommand
from buildbot.steps.shell import ShellCommand
from twisted.internet import defer

GITCACHE_BUILD_LOCK = MasterLock('gitcache_build')


class CheckGitCachePresence(ShellCommand):
    """Check presence of gitcache on local docker instance."""

    def __init__(self, **kwargs):
        kwargs.setdefault('flunkOnFailure', False)
        kwargs.setdefault('haltOnFailure', False)
        kwargs.setdefault('hideStepIf', lambda results, s: results == SUCCESS)
        kwargs.setdefault('name', 'check presence of gitcache')
        super(CheckGitCachePresence, self).__init__(
            command='docker ps --format {{.Names}} --filter name=%s' %
                    util.env.GITCACHE_HOSTNAME,
            **kwargs)
        self.observer = logobserver.BufferLogObserver()
        self.addLogObserver('stdio', self.observer)

    @defer.inlineCallbacks
    def run(self):
        result = yield super(CheckGitCachePresence, self).run()

        if (result == SUCCESS and
                util.env.GITCACHE_HOSTNAME not in self.observer.getStdout()):
            self.build.addStepsAfterCurrentStep([
                MasterShellCommand(
                    name='build gitcache image',
                    locks=[GITCACHE_BUILD_LOCK.access('exclusive')],
                    hideStepIf=lambda results, s: results == SUCCESS,
                    command='docker build -t gitcache_img %s' %
                            util.env.GITCACHE_BUILDDIR),
                MasterShellCommand(
                    name='cleanup gitcache left-overs',
                    flunkOnFailure=False,
                    haltOnFailure=False,
                    locks=[GITCACHE_BUILD_LOCK.access('exclusive')],
                    hideStepIf=lambda results, s: results == SUCCESS,
                    command='docker rm %s' % util.env.GITCACHE_BUILDDIR),
                MasterShellCommand(
                    name='launch new gitcache container',
                    locks=[GITCACHE_BUILD_LOCK.access('exclusive')],
                    hideStepIf=lambda results, s: results == SUCCESS,
                    command=('docker run --detach --name %s '
                             '--publish %s:80 gitcache_img') % (
                                 util.env.GITCACHE_HOSTNAME,
                                 util.env.GITCACHE_PORT))
            ])
        defer.returnValue(result)
