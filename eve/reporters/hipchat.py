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

from buildbot.process.results import (CANCELLED, EXCEPTION, FAILURE, RETRY,
                                      SKIPPED, SUCCESS, WARNINGS)
from buildbot.util.httpclientservice import HTTPClientService
from twisted.internet import defer
from twisted.logger import Logger

from eve.reporters.base import BaseBuildStatusPush, BuildStatusPushMixin


class HipChatBuildStatusPush(BaseBuildStatusPush, BuildStatusPushMixin):
    """Send build result to HipChat build status API."""

    name = 'HipChatBuildStatusPush'
    logger = Logger('eve.steps.HipChatBuildStatusPush')
    attributes = []
    COLOR_STYLE_CORRESP = {
        'green': 'lozenge-success',
        'orange': 'lozenge-current',
        'red': 'lozenge-error',
        'white': 'lozenge',
        'purple': 'lozenge-error',
        'pink': 'lozenge-error',
        'brown': 'lozenge-moved',
        'blue': 'lozenge-complete',
        'gray': 'lozenge',
    }
    HIPCHAT_COLOR_CORRESP = {
        SUCCESS: 'green',
        WARNINGS: 'yellow',
        FAILURE: 'red',
        SKIPPED: 'gray',
        EXCEPTION: 'purple',
        RETRY: 'purple',
        CANCELLED: 'gray',
        None: 'gray',
    }

    def __init__(self, stages, room_id, token, **kwargs):
        self.room_id = room_id
        self.token = token
        self.stages = [stages] if isinstance(stages, basestring) else stages
        super(HipChatBuildStatusPush, self).__init__(**kwargs)

    def add_tag(self, name, value, icon, color=None):
        attr = dict(label=name, value=dict(label=value))
        if color in self.COLOR_STYLE_CORRESP:
            attr['value']['style'] = self.COLOR_STYLE_CORRESP[color]
        if icon:
            attr['value']['icon'] = dict(url=icon)
        self.attributes.append(attr)

    def filterBuilds(self, build):
        return self._filterBuilds(
            super(HipChatBuildStatusPush, self).filterBuilds, build)

    @defer.inlineCallbacks
    def send(self, build):
        """Send build status to HipChat."""
        if not self.room_id or not self.token:
            self.logger.info('Hipchat status not sent'
                             ' (HIPCHAT_* variables not defined))')
            return

        self.attributes = []
        key, result, title, summary, description = self.gather_data(build)

        card = dict(
            style='application',
            url=build['url'],
            format='medium',
            id=key,
            title=title,
            description=dict(format='text', value=description),
            attributes=self.attributes,
            activity=dict(html=summary))

        data = dict(
            message=summary,
            name=key,
            message_format='text',
            notify=True,
            card=card,
            color=self.HIPCHAT_COLOR_CORRESP[result])

        url = 'https://api.hipchat.com/v2/room/%s/notification' % self.room_id

        http_service = yield HTTPClientService.getService(self.master, url)
        response = yield http_service.post('', json=data, params={
            'auth_token': self.token
        })

        if response.code != 204:
            raise Exception(
                "{response.code}: unable to send status to HipChat: "
                "{url}\nRequest:\n{request}\nResponse:\n{response.content}".
                format(request=data, response=response, url=url))

        self.logger.info('HipChat status sent')
