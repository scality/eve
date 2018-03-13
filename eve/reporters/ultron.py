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

        if build['results'] in ('SUCCESSFUL', 'WARNINGS'):
            result = 'success'
        elif build['results'] == 'RETRY':
            result = 'timedout'
        else:
            result = 'failed'

        if self.req_login:
            auth = (self.req_login, self.req_password)
        else:
            auth = None
        url = self.req_url
        data = {
            'payload': {
                'build_url': build['url'],
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
