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
"""Buildbot REST API client.

for more info on the API, see `buildbot REST API documentation`_

.. _buildbot REST API documentation:
  http://docs.buildbot.net/latest/developer/rest.html

"""

from __future__ import print_function

import json
import time

import requests
import urllib3
from requests.exceptions import ConnectionError
from urllib3.exceptions import InsecureRequestWarning

RESULT_CODES = [
    'success', 'warnings', 'failure', 'skipped', 'exception', 'retry',
    'cancelled'
]
# Hack to remove a lot of warnings in stdout while testing
urllib3.disable_warnings(InsecureRequestWarning)


class BuildbotDataAPI(object):
    """Class to interact with a Buildbot master through its REST API."""

    def __init__(self, url):
        self.url = url
        assert url.endswith('/')
        self.api_url = "{0}api/v2".format(self.url)

        self.session = requests.Session()

    def login(self, user, password):
        """Retrieve the authenticated cookie in the session."""
        res = self.session.get(self.url + "auth/login", auth=(user, password))
        res.raise_for_status()

    def logout(self):
        """Remove the authenticated cookie from the session."""
        res = self.session.get(self.url + "auth/logout")
        res.raise_for_status()

    def post(self, route, method, params=None):
        """Post data to the REST API."""
        data = {
            'id': 999,
            # sequence number doesn't matter for synchronous requests
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }

        res = self.session.post(self.api_url + route, json=data)
        res.raise_for_status()
        return res.json()['result']

    def get(self, route, get_params=None, raw=False):
        """Get data from the REST API."""
        print('requesting {} get params {}', self.api_url + route, get_params)
        res = self.session.get(
            self.api_url + route,
            headers={"Accept": "application/json"},
            params=get_params)
        res.raise_for_status()

        if raw:
            return res.text

        object_name = route.split('/')[-1]

        if object_name == '':
            return res.json()

        if object_name.isdigit():
            object_name = route.split('/')[-2]

        return res.json()[object_name]

    def getw(self, route, get_params=None, retry=180, expected_count=1):
        """Wait for and return a given number of results from the REST API."""
        for i in range(retry):
            try:
                res = self.get(route=route, get_params=get_params)
            except ConnectionError:
                if i == retry - 1:
                    raise
                print('waiting for', self.api_url + route,
                      'to be available...', get_params)
                time.sleep(1)
                continue

            if expected_count is None:
                return res

            cur_len = len(res)
            if cur_len == expected_count:
                if expected_count == 1:
                    return res[0]
                return res

            if cur_len > expected_count:
                raise Exception('Found more objects than expected {} > {}'.
                                format(cur_len, expected_count))
            print('waiting for', route, get_params, cur_len, 'out of',
                  expected_count)
            time.sleep(1)

        raise Exception('The route {} exists but never reached the expected '
                        'count'.format(self.api_url + route))

    def get_builder(self, name='bootstrap'):
        """Get builder named name from the Buildbot's API."""
        return self.get('/builders', {'name': name})[0]

    def get_scheduler(self, name):
        """Get scheduler named name from the Buildbot's API."""
        return self.get('/schedulers', {'name': name})[0]

    def get_builds(self, builder='bootstrap'):
        builder = self.get_builder(builder)
        return self.get('/builders/%d/builds' % builder['builderid'])

    def get_build(self, builder='boostrap', branch=None, timeout=10):
        """Wait for build to start and return its infos."""
        the_build = None
        for _ in range(timeout):
            if the_build:
                break
            builds = self.get_builds(builder=builder) or []
            for build in builds:
                prop_branch = build['properties'].get('branch')
                if not branch or (prop_branch
                                  and str(prop_branch[0]) == branch):
                    the_build = build
                    break
            else:
                time.sleep(1)
                print('waiting for build to start on {}'.format(self.url))

        else:
            raise Exception('unable to find build, '
                            'builder=%s, branch=%s' % (builder, branch))
        return the_build

    def get_build_for_id(self, buildid):
        return Build.find(
            self,
            get_params={
                'buildid': buildid,
                'property': '*'
            }
        )

    def get_finished_build(self, builder='bootstrap', branch=None, timeout=60):
        for _ in range(timeout):
            build = self.get_build(builder, branch, timeout)
            if build['results'] is None:
                time.sleep(1)
            else:
                break
        else:
            raise Exception('Timeout while waiting for build to finish')
        return build

    def get_build_properties(self, build):
        """Return properties from specified build."""
        return self.get('/builds/%d/properties' % build['buildid'])[0]

    def get_build_steps(self, build):
        """Return steps from specified build."""
        return self.get('/builders/%d/builds/%d/steps' %
                        (build['builderid'], build['number']))

    def get_step(self, name, build):
        """Return matching step from specified builder and build number."""
        steps = self.get_build_steps(build)
        step = [s for s in steps if s["name"] == name]
        if not step:
            raise Exception('unable to find build step with this name')
        return step[0]

    def webhook(self, git_repo, revision=''):
        """Notify Eve's bitbucket hook of a new change."""
        commits = []
        for line in git_repo.loglines:
            author, message, rev, _ = line.split('|')
            if not rev.startswith(revision):
                continue
            commits.append({
                'new': {
                    'type': 'branch',
                    'target': {
                        'hash': rev,
                        'author': {
                            'raw': author
                        },
                        'message': message,
                        'links': {
                            'html': {
                                'href': rev
                            }
                        },
                    },
                    'name': git_repo.branch
                }
            })

        payload = {
            'repository': {
                'links': {
                    'html': {
                        'href': 'http://www.example.com/'
                    }
                },
                'scm': 'git',
                'project': {
                    'name': 'TEST'
                },
            },
            'push': {
                'changes': commits
            },
            'commits': commits,
        }
        res = requests.post(
            self.url + 'change_hook/bitbucket', data=json.dumps(payload))
        res.raise_for_status()

    def force(self, **kwargs):
        """Force a build.

        Args:
            arguments accepted by the force API (see `buildbot forcescheduler's
            documentation`_).

        Returns:
            The Buildset that has been added.

        .. _buildbot forcescheduler's documentation:
            http://docs.buildbot.net/latest/developer/rest.html#forcescheduler

        """
        path = '/forceschedulers'
        scheds = self.getw(path, expected_count=2)
        force_sched_name = None
        for sched in scheds:
            sched_name = sched['name']
            if sched_name != '__Janitor_force':
                force_sched_name = sched_name
                break
        res = self.post('{}/{}'.format(path, force_sched_name),
                        'force', kwargs)

        buildset = BuildSet(api=self, id_=res[0])
        return buildset


class ApiResource(object):
    base_path = None
    results_field = None
    id_field = None
    default_get_params = None

    def __init__(self, api, id_, url_params=None):
        """Represent a Resource from the API.

        Args:
            api: The API instance.
            id_: The ID of the resource.
            url_params (dict): Some objects needed to specify additional
                parameters on the url to be retrieved (e.g. to retrieve a step,
                you need to specify a buildid).

        """
        self._api = api
        self._id = id_
        self._dict = None
        if url_params is None:
            url_params = {}
        url = self.__class__.base_path.format(**url_params)
        self._url = '{}/{}'.format(url, self._id)
        self._full_url = '{}{}'.format(api.api_url, self._url)

    @classmethod
    def find(cls, api, url_params=None, get_params=None, expected_count=1):
        """Find one or more resources from the API.

        Args:
            api: The API object.
            url_params (dict): See __init__ docstring.
            get_params (dict): The get parameters to add to the URL.
            expected_count (int): The number of resources that are expected
                (default to 1).

        Returns:
            If expected_count == 1, returns a single resource. Otherwise,
            returns a list of resources.

        Raises:
            Exception: If the expected_count is not matched.

        """
        if url_params is None:
            url_params = {}
        if get_params is None:
            get_params = {}
        res = api.getw(
            cls.base_path.format(**url_params),
            get_params,
            expected_count=expected_count)
        if expected_count == 1:
            return cls(api, res[cls.id_field], url_params=url_params)
        else:
            return [
                cls(api, dict_[cls.id_field], url_params=url_params)
                for dict_ in res
            ]

    def _refresh(self):
        self._dict = self._api.getw(
            self._url, get_params=self.default_get_params)

    def __getattr__(self, item):
        if self._dict is None:
            self._refresh()
        try:
            return self._dict[item]
        except KeyError:
            raise AttributeError('{} does not exist'.format(item))

    def wait_for_finish(self, timeout=360):
        """Wait for a resource until it has results.

        Args:
            timeout (int): The number of seconds to wait for it.

        """
        if self.results_field is None:
            return self
        for _ in range(timeout):
            self._refresh()
            if self._dict[self.results_field] is not None and \
                    self._dict[self.results_field] != -1:
                return self
            print('wating for {} to finish'.format(self._full_url))
            time.sleep(1)
        raise Exception('waited {} seconds for {} but it never finished'.
                        format(timeout, self._full_url))

    @property
    def result(self):
        """Wait for and return the result of the resource."""
        assert self.results_field is not None
        self.wait_for_finish()
        result_code = self._dict[self.results_field]
        return RESULT_CODES[result_code]


class BuildSet(ApiResource):
    """Represent a BuildSet API object."""

    base_path = '/buildsets'
    results_field = 'results'
    id_field = 'bsid'

    @property
    def buildrequest(self):
        return BuildRequest.find(
            self._api, get_params={'buildsetid': self.bsid})


class BuildRequest(ApiResource):
    """Represent a BuildRequest API object."""

    base_path = '/buildrequests'
    results_field = 'results'
    id_field = 'buildrequestid'

    @property
    def build(self):
        return Build.find(
            self._api,
            get_params={
                'buildrequestid': self.buildrequestid,
                'property': '*'
            })


class Build(ApiResource):
    """Represent a Build API object."""

    base_path = '/builds'
    results_field = 'results'
    id_field = 'buildid'
    default_get_params = {'property': '*'}

    @property
    def children(self):
        """Return the builds which the parent_buildid is this instance."""
        return BuildSet.find(
            self._api,
            get_params={'parent_buildid': self.buildid},
            expected_count=None)

    @property
    def steps(self):
        """Return the steps of this build."""
        return Step.find(
            self._api,
            url_params={'buildid': self.buildid},
            expected_count=None)

    @property
    def first_failing_step(self):
        """Return the first step that failed, or raises an exception."""
        for step in self.steps:
            if step.results not in (0, 1, 3):  # success, warning, skipped
                return step
        raise Exception('There is no failing steps under this build')


class Step(ApiResource):
    """Represent a Step API object."""

    base_path = '/builds/{buildid}/steps'
    results_field = 'results'
    id_field = 'number'

    def rawlog(self, log_slug):
        """Return the step log contents as text.

        Args:
            log_slug (str): The name of the log. e.g., 'stdio'.

        """
        route = (self.base_path + '/{step_number}/logs/{log_slug}/raw').format(
            buildid=self.buildid, step_number=self.number, log_slug=log_slug)
        return self._api.get(route=route, raw=True)
