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

import datetime

from buildbot.plugins import util
from buildbot.www.auth import NoAuth, UserPasswordAuth
from buildbot.www.authz import Authz, Forbidden
from buildbot.www.authz.endpointmatchers import (AnyEndpointMatcher,
                                                 EndpointMatcherBase)
from buildbot.www.authz.roles import RolesFromGroups, RolesFromUsername
from buildbot.www.oauth2 import BitbucketAuth, GitHubAuth
from twisted.internet import defer


class DenyRebuildIntermediateBuild(EndpointMatcherBase):
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

        Args:
            root_builder_name (str): Name of the root builder.

        """
        self.root_builder_name = root_builder_name

        EndpointMatcherBase.__init__(self, **kwargs)

    @defer.inlineCallbacks
    def match_BuildEndpoint_rebuild(self, epobject, epdict, _):
        """Disallow rebuild of anything else than the root builder.

        Raises:
            Forbidden: If the builder name is an intermediate build of the
                given root builder.

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
            raise Forbidden(
                'This builder is not allowed to be rebuilt.'
                ' Please select the "{0}" builder.'.format(
                    builder['name']
                )
            )


def www():
    try:
        port = 'tcp:{}'.format(int(util.env.HTTP_PORT))
    except ValueError:
        port = util.env.HTTP_PORT
    return {
        'port': port,
        'plugins': {},
        'change_hook_dialects': {
            'bitbucket': True,
            'github': {}
        },
        'debug': True,
        'cookie_expiration_time': datetime.timedelta(weeks=1),
    }


def auth():
    if util.env.OAUTH2_CLIENT_ID:
        auth_method = {
            'bitbucket': BitbucketAuth,
            'github': GitHubAuth,
        }[util.env.OAUTH2_PROVIDER.lower()]
        return auth_method(
            util.env.OAUTH2_CLIENT_ID,
            util.env.OAUTH2_CLIENT_SECRET
        )

    if util.env.WWW_PLAIN_LOGIN:
        return UserPasswordAuth({
            util.env.WWW_PLAIN_LOGIN: util.env.WWW_PLAIN_PASSWORD})

    return NoAuth()


def authz():
    if not util.env.OAUTH2_CLIENT_ID and not util.env.WWW_PLAIN_LOGIN:
        return Authz()

    if util.env.OAUTH2_CLIENT_ID:
        role_matchers = [RolesFromGroups()]
    else:
        util.env.OAUTH2_GROUP = 'admin'
        role_matchers = [RolesFromUsername(
            roles=[util.env.OAUTH2_GROUP],
            usernames=[util.env.WWW_PLAIN_LOGIN],
        )]
    return Authz(
        allowRules=[
            DenyRebuildIntermediateBuild(util.env.BOOTSTRAP_BUILDER_NAME,
                                         role='*'),
            AnyEndpointMatcher(role=util.env.OAUTH2_GROUP),
        ],
        roleMatchers=role_matchers,
    )
