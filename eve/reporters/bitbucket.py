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

from eve.reporters.base import BaseBuildStatusPush


class BitbucketBuildStatusPush(BaseBuildStatusPush):
    """Send build result to bitbucket build status API."""

    base_url = "https://api.bitbucket.org"
    name = 'BitbucketBuildStatusPush'
    description_suffix = ''
    logger = Logger('eve.steps.BitbucketBuildStatusPush')
    BITBUCKET_STATUS_CORRESP = {
        SUCCESS: 'SUCCESSFUL',
        WARNINGS: 'SUCCESSFUL',
        FAILURE: 'FAILED',
        SKIPPED: 'STOPPED',
        EXCEPTION: 'FAILED',
        CANCELLED: 'STOPPED',
        RETRY: 'INPROGRESS',
        None: 'INPROGRESS',
    }

    def __init__(self, login, password, **kwargs):
        self.login = login
        self.password = password
        super(BitbucketBuildStatusPush, self).__init__(**kwargs)

    def forge_url(self, build):
        """Forge the BB API URL on which the build status will be posted."""
        sha1 = build['buildset']['sourcestamps'][0]['revision']
        return '%(base_url)s/2.0/repositories/' \
               '%(repo_owner)s/%(repo_name)s/commit/%(sha1)s/statuses/build' \
               % {
                   'base_url': self.base_url,
                   'repo_owner': 'scality',
                   'repo_name': self.repo,
                   'sha1': sha1,
               }

    def add_tag(self, name, value, icon, color=None):
        name_value = '[%s: %s]' % (name, value)
        self.description_suffix = name_value + self.description_suffix

    @defer.inlineCallbacks
    def send(self, build):
        """Send build status to Bitbucket."""
        self.description_suffix = ''
        key, result, _, summary, description = self.gather_data(build)
        data = {
            'state': self.BITBUCKET_STATUS_CORRESP[result],
            'key': key,
            'name': summary[:255],
            'url': build['url'],
            'description': description + self.description_suffix,
        }
        url = self.forge_url(build)

        http_service = yield HTTPClientService.getService(
            self.master, url, auth=(self.login, self.password))
        response = yield http_service.post('', json=data)
        # 200 means that the key already exists
        # 201 means that the key has been created successfully
        if response.code not in (200, 201):
            raise Exception(
                "{response.code}: unable to send status to Bitbucket: "
                "{url}\nRequest:\n{request}\nResponse:\n{response.content}".
                format(request=data, response=response, url=url))
        self.logger.info('Bitbucket status sent (%s:%s on %s)' % (
            self.BITBUCKET_STATUS_CORRESP[result],
            key,
            url))
