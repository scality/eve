# coding: utf-8
"""Buildbot REST API client.

for more info on the API, see `buildbot REST API documentation`_

.. _buildbot REST API documentation:
  http://docs.buildbot.net/latest/developer/rest.html
"""

from __future__ import print_function

import json
import time

import requests
from requests.exceptions import ConnectionError
from requests.packages.urllib3.exceptions import InsecureRequestWarning

RESULT_CODES = [
    'success', 'warnings', 'failure', 'skipped', 'exception', 'retry',
    'cancelled'
]
# Hack to remove a lot of warnings in stdout while testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class BuildbotDataAPI(object):
    """Class to interact with a Buildbot master through its REST API."""

    def __init__(self, uri):
        self.uri = uri
        assert uri.endswith('/')
        self.api_uri = "{0}api/v2".format(self.uri)

        self.session = requests.Session()

    def login(self, user, password):
        """Retreive the authenticated cookie in the session."""
        res = self.session.get(self.uri + "auth/login", auth=(user, password))
        res.raise_for_status()

    def logout(self):
        """Remove the authenticated cookie from the session."""
        res = self.session.get(self.uri + "auth/logout")
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

        res = self.session.post(self.api_uri + route, json=data)
        res.raise_for_status()
        return res.json()['result']

    def get(self, route, get_params=None):
        """Get data from the REST API."""
        print(self.api_uri + route, get_params)
        res = self.session.get(
            self.api_uri + route,
            headers={"Accept": "application/json"},
            params=get_params)
        res.raise_for_status()

        object_name = route.split('/')[-1]

        if object_name == '':
            return res.json()

        if object_name.isdigit():
            object_name = route.split('/')[-2]

        return res.json()[object_name]

    def getw(self, route, get_params=None, retry=60, expected_count=1):
        """Get data from the REST API."""
        for i in xrange(retry):
            try:
                res = self.get(route=route, get_params=get_params)
            except ConnectionError:
                if i == retry - 1:
                    raise
                print('waiting for', self.api_uri + route,
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
                        'count'.format(self.api_uri + route))

    def get_element_id_from_name(self, route, name, id_key, name_key='name'):
        """Get the ID of an entity using its name."""
        # The top level of every response is an object whose keys are the
        # plural name of the resource types (hence the get(route)[route]).
        # e.g. GET api/v2/schedulers
        # {
        #     "meta": {
        #         "total": 2
        #     },
        #     "schedulers": [
        #         {...},
        #         {...}
        #     ]
        # }
        elements = self.get(route)[route]
        for elem in elements:
            if elem[name_key] == name:
                _id = elem[id_key]
                break
        else:
            raise Exception('element not found')
        return _id

    def get_build_result(self,
                         builder='bootstrap',
                         branch=None,
                         expected_result='success'):
        """Get the result of the build `build_number`."""
        for _ in range(900):
            build = self.get_build(builder=builder, branch=branch)
            if build['state_string'] == 'finished' and \
                    build['results'] is not None:
                break
            time.sleep(1)
            print('waiting for build to finish on {}'.format(self.uri))
        else:
            raise Exception('Build took too long')
        result_codes = [
            'success', 'warnings', 'failure', 'skipped', 'exception', 'retry',
            'cancelled'
        ]
        assert result_codes[build['results']] == expected_result
        return build

    def get_builder(self, name):
        """Get builder named name from the Buildbot's API."""
        return self.get('/builders?name=%s' % name)['builders'][0]

    def get_scheduler(self, name):
        """Get scheduler named name from the Buildbot's API."""
        return self.get('/schedulers?name=%s' % name)['schedulers'][0]

    def get_builds(self, builder='bootstrap'):
        builder = self.get_builder(builder)
        return self.get('/builds?'
                        'property=*'
                        '&builderid=%d' % (builder['builderid']))['builds']

    def get_build(self, builder='boostrap', branch=None):
        """Wait for build to start and return its infos."""

        the_build = None
        for _ in range(60):
            if the_build:
                break
            builds = self.get_builds(builder=builder)
            the_build = None
            for build in builds:
                prop_branch = build['properties'].get('/branch')
                print(branch, prop_branch)
                if not branch or (prop_branch and
                                  str(prop_branch[0]) == branch):
                    the_build = build
                    break
            else:
                time.sleep(1)
                print('waiting for build to start on {}'.format(self.uri))

        else:
            raise Exception('unable to find build, '
                            'builder=%s, branch=%s' % (builder, branch))
        return the_build

    def get_build_steps(self, builder='bootstrap', build_number=1):
        """Returns steps from specified builder and build."""
        builder = self.get_builder(builder)
        try:
            return self.get('builders/%d/builds/%d/steps' %
                            (builder['builderid'], build_number))['steps']
        except KeyError:
            raise Exception('unable to find build steps, '
                            'builderid=%d, build_number=%d' %
                            (builder['builderid'], build_number))

    def get_step(self, name, builder='bootstrap', build_number=1):
        """Returns matching step from specified builder and build number."""
        steps = self.get_build_steps(
            builder=builder, build_number=build_number)
        step = [s for s in steps if s["name"] == name]
        if not step:
            raise Exception('unable to find build step %r, '
                            'builderid=%d, build_number=%d' %
                            (name, builder['builderid'], build_number))
        return step[0]

    def webhook(self, git_repo):
        """Notify Eve's bitbucket hook of a new change."""
        commits = []
        for line in git_repo.loglines:
            author, message, revision, _ = line.split('|')
            commits.append({
                'new': {
                    'type': 'branch',
                    'target': {
                        'hash': revision,
                        'author': {
                            'raw': author
                        },
                        'message': message,
                        'links': {
                            'html': {
                                'href': revision
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
            self.uri + 'change_hook/bitbucket', data=json.dumps(payload))
        res.raise_for_status()

    def force(self, branch, reason='testing'):
        force_sched_name = self.getw('/forceschedulers')['name']
        res = self.post(
            '/forceschedulers/{}'.format(force_sched_name),
            'force', {
                'branch': branch,
                'owner': 'John Doe <john@doe.net>',
                'reason': reason
            })  # yapf: disable

        buildset = BuildSet(self, res[0])
        return buildset


class ApiResource(object):
    base_path = None
    results_field = None
    id_field = None
    default_get_params = None

    def __init__(self, api, id_, url_params=None):
        self._api = api
        self._id = id_
        self._dict = None
        if url_params is None:
            url_params = {}
        url = self.__class__.base_path.format(**url_params)
        self._url = '{}/{}'.format(url, self._id)
        self._full_url = '{}{}'.format(api.api_uri, self._url)

    @classmethod
    def find(cls, api, url_params=None, get_params=None, expected_count=1):
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
        return self._dict[item]

    def wait_for_finish(self, timeout=60):
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
        assert self.results_field is not None
        self.wait_for_finish()
        result_code = self._dict[self.results_field]
        return RESULT_CODES[result_code]


class BuildSet(ApiResource):
    base_path = '/buildsets'
    results_field = 'results'
    id_field = 'bsid'

    @property
    def buildrequest(self):
        return BuildRequest.find(
            self._api, get_params={'buildsetid': self.bsid})


class BuildRequest(ApiResource):
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
    base_path = '/builds'
    results_field = 'results'
    id_field = 'buildid'
    default_get_params = {'property': '*'}

    @property
    def children(self):
        return BuildSet.find(
            self._api,
            get_params={'parent_buildid': self.buildid},
            expected_count=None)

    @property
    def steps(self):
        return Steps.find(
            self._api,
            url_params={'buildid': self.buildid},
            expected_count=None)

    @property
    def first_failing_step(self):
        for step in self.steps:
            if step.results != 0:
                return step
        raise Exception('There is no failing steps under this build')


class Steps(ApiResource):
    base_path = '/builds/{buildid}/steps'
    results_field = 'results'
    id_field = 'number'
