import buildbot.www.authz as bb_authz
import buildbot.www.authz.endpointmatchers as bb_endpointmatchers
from twisted.internet import defer


class DenyRebuildBuildEndpointMatcher(bb_endpointmatchers.EndpointMatcherBase):
    """Build endpoint matcher class to deny rebuild.

    This class differs from `~.endpointmatchers.RebuildBuildEndpointMatcher`.
    This latter class is incomplete and doesn't match any builder.

    `~.endpointmatchers.EndpointMatcherBase` is built to return if the
    endpoint match.
    It is the responsibility of :meth:`~.authz.Autz.assertUserAllowed`
    to deny access if the role doesn't match.

    Here we need to deny the endpoint for all roles and allow it only
    for the given builders.
    """
    def __init__(self, allow_builders=None, **kwargs):
        """`DenyRebuildBuildEndpointMatcher` constructor.

        :args allow_builder: List of allowed builders name

        All the other builders will be denied.
        """
        self.allow_builders = allow_builders or []

        bb_endpointmatchers.EndpointMatcherBase.__init__(self, **kwargs)

    @defer.inlineCallbacks
    def match_BuildEndpoint_rebuild(self, epobject, epdict, _):
        """Called by `~.EndpointMatcherBase.match` for rebuild endpoint.

        :raises Forbidden: If the builder name doesn't match
                           ``allow_builders``.
        """
        build = yield epobject.get({}, epdict)
        builder = yield self.master.data.get(
            ('builders', build['builderid'])
        )

        for allow_builder in self.allow_builders:
            if self.authz.match(builder['name'], allow_builder):
                break
        else:
            raise bb_authz.Forbidden(
                "This builder is not allowed to be rebuilt"
            )

        if self.role:
            match = bb_endpointmatchers.Match(self.master, build=build)
        else:
            match = None
        defer.returnValue(match)
