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

import json

from buildbot.www.hooks import bitbucket
from twisted.python import log


def getChanges(request, _options=None):
    """Catch a POST request from BitBucket and start a build process

    Check the URL below if you require more information about payload
    https://confluence.atlassian.com/display/BITBUCKET/POST+Service+Management

    :param request: the http request Twisted object
    :param _options: additional options

    """
    log.msg('Processing changes from bitbucket')
    payload = json.loads(request.content.read())
    repo_url = payload['repository']['links']['html']['href']
    log.msg('repo_url:', repo_url)
    project = payload['repository']['project']['name']

    changes = []
    commits = set()
    for change in payload['push']['changes']:
        new = change.get('new', None)
        if new is None:
            continue
        if new['type'] != u'branch':
            continue
        log.msg('found branch change!')
        target = new['target']

        if target['hash'] in commits:
            # FIXME: temporary fix to have only one build per commit
            log.msg('skipping branch %s: commit %s already '
                    'scheduled for building' % (new['name'], target['hash']))
            continue

        commits.add(target['hash'])
        change = {
            'author': target['author']['raw'],
            'branch': new['name'],
            'files': [],
            'comments': target['message'],
            'revision': target['hash'],
            'revlink': target['links']['html']['href'],
            'repository': repo_url,
            'project': project
        }
        log.msg(change)

        changes.append(change)

    return (changes, payload['repository']['scm'])


def patch():
    bitbucket.getChanges = getChanges
