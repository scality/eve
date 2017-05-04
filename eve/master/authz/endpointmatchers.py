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

import buildbot.www.authz as bb_authz
import buildbot.www.authz.endpointmatchers as bb_endpointmatchers
from twisted.internet import defer


class DenyRebuildIntermediateBuild(bb_endpointmatchers.EndpointMatcherBase):
    """Build endpoint matcher class to deny rebuild on intermediate build.

    This class differs from `~.endpointmatchers.RebuildBuildEndpointMatcher`.
    This latter class is incomplete and doesn't match any builder.

    `~.endpointmatchers.EndpointMatcherBase` is built to return if the
    endpoint match.
    It is the responsibility of :meth:`~.authz.Autz.assertUserAllowed`
    to deny access if the role doesn't match.

    Here we need to deny the endpoint for all roles if the build is an
    intermediate build of the given builder.
    """
    def __init__(self, root_builder_name, **kwargs):
        """`DenyRebuildBuildEndpointMatcher` constructor.

        :args root_builder_name: Name of the root builder.
        """
        self.root_builder_name = root_builder_name

        bb_endpointmatchers.EndpointMatcherBase.__init__(self, **kwargs)

    @defer.inlineCallbacks
    def match_BuildEndpoint_rebuild(self, epobject, epdict, _):
        """Called by `~.EndpointMatcherBase.match` for rebuild endpoint.

        :raises Forbidden: If the builder name is an intermediate
                             build of the given root builder.
        """
        build = yield epobject.get({}, epdict)
        buildrequest = yield self.master.data.get(
            ('buildrequests', build['buildrequestid'])
        )
        buildset = yield self.master.data.get(
            ('buildsets', buildrequest['buildsetid'])
        )

        if buildset['parent_buildid'] is None:
            defer.returnValue(None)

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

        builder = yield self.master.data.get(
            ('builders', build['builderid'])
        )

        if self.authz.match(builder['name'], self.root_builder_name):
            raise bb_authz.Forbidden(
                'This builder is not allowed to be rebuilt.'
                ' Please select the "{0}" builder.'.format(
                    builder["name"]
                )
            )
