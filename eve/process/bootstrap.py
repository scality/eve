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

from twisted.internet import defer


class BootstrapMixin:

    @defer.inlineCallbacks
    def _get_bootstrap(self, buildid):
        """Retrieve the bootstrap builds.

        Returns a tuple with the build, buildrequest, and the buildset.

        """
        build = yield self.master.data.get(('builds', buildid))
        buildrequest = yield self.master.data.get(
            ('buildrequests', build['buildrequestid'])
        )
        buildset = yield self.master.data.get(
            ('buildsets', buildrequest['buildsetid'])
        )
        while buildset['parent_buildid'] is not None:
            build = yield self.master.data.get(
                ('builds', buildset['parent_buildid'])
            )
            buildrequest = yield self.master.data.get(
                ('buildrequests', build['buildrequestid'])
            )
            buildset = yield self.master.data.get(
                ('buildsets', buildrequest['buildsetid'])
            )

        defer.returnValue((build, buildrequest, buildset))

    @defer.inlineCallbacks
    def getBootstrapBuildRequest(self, buildid):
        _, buildrequest, _ = yield self._get_bootstrap(buildid)
        defer.returnValue(buildrequest)

    @defer.inlineCallbacks
    def getBootstrapBuild(self, buildid):
        build, _, _ = yield self._get_bootstrap(buildid)
        defer.returnValue(build)

    @defer.inlineCallbacks
    def setBootstrapProperty(self, buildid, property, value, source):
        """Set a property on the bootstrap."""
        bootstrap_build = yield self.getBootstrapBuild(buildid)
        res = yield self.master.db.builds.setBuildProperty(
            bootstrap_build['buildid'], property, value, source
        )
        defer.returnValue(res)
