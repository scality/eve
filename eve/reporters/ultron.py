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

from urlparse import urlparse, urlunparse

from buildbot.process.results import (CANCELLED, EXCEPTION, FAILURE, RETRY,
                                      SKIPPED, SUCCESS, WARNINGS)
from buildbot.util.httpclientservice import HTTPClientService
from twisted.internet import defer
from twisted.logger import Logger

from eve.reporters.base import BaseBuildStatusPush, BuildStatusPushMixin


class UltronBuildStatusPush(BaseBuildStatusPush, BuildStatusPushMixin):
    """Send build result to Scality Ultron status API."""

    name = 'UltronBuildStatusPush'
    logger = Logger('eve.steps.HttpBuildStatusPush')

    def __init__(self, stages, req_login, req_password, req_url, **kwargs):
        self.stages = [stages] if isinstance(stages, basestring) else stages
        self.req_login = req_login
        self.req_password = req_password
        self.req_url = req_url
        super(UltronBuildStatusPush, self).__init__(**kwargs)

    def filterBuilds(self, build):
        return self._filterBuilds(
            super(UltronBuildStatusPush, self).filterBuilds, build)

    @defer.inlineCallbacks
    def send(self, build):
        """Send build status to Ultron."""

        result = {
            SUCCESS: 'success',
            WARNINGS: 'success',
            FAILURE: 'failed',
            SKIPPED: 'failed',
            EXCEPTION: 'failed',
            CANCELLED: 'failed',
            RETRY: 'failed',
            None: 'running',
        }[build['results']]

        if self.req_login:
            auth = (self.req_login, self.req_password)
        else:
            auth = None
        url = self.req_url
        root_buildrequest_url = yield self._get_root_buildrequest_url_for(
            build)
        data = {
            'payload': {
                'build_url': root_buildrequest_url,
                'outcome': result,
            }
        }

        http_service = yield HTTPClientService.getService(
            self.master, url, auth=auth)
        response = yield http_service.post('', json=data)

        if response.code != 200:
            raise Exception(
                "{response.code}: unable to send status: "
                "{url}\nRequest:\n{request}\nResponse:\n{response.content}".
                format(request=data, response=response, url=url))

        self.logger.info('Ultron status sent (%s on %s)' % (result, url))

    @defer.inlineCallbacks
    def _get_root_buildrequest_url_for(self, build):
        base_url = urlparse(build['url'])[:-1]
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

        br_path = ('/buildrequests/%d?redirect_to_build=true' %
                   buildrequest['buildrequestid'])
        defer.returnValue(urlunparse(base_url + (br_path,)))
