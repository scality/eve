#coding: utf-8
"""Buildbot REST API client.

for more info on the API, see `buildbot REST API documentation`_

.. _buildbot REST API documentation:
  http://docs.buildbot.net/latest/developer/rest.html
"""

import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Hack to remove a lot of warnings in stdout while testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class BuildbotDataAPI(object):
    """Class to interact with a Buildbot master through its REST API."""

    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
        }
        self.auth = None

    def add_auth(self, user, password):
        """Use given `user` and `password` for HTTP basic auth."""
        self.auth = HTTPBasicAuth(user, password)

    def post(self, route, method, params=None):
        """Post data to the REST API."""
        data = {
            'id': 1,  # sequence number doesn't matter for synchronous requests
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }

        res = requests.post(self.base_url + route, json=data,
                            headers=self.headers, auth=self.auth)
        res.raise_for_status()
        return res.json()

    def get(self, route):
        """Get data from the REST API."""
        res = requests.get(self.base_url + route, headers=self.headers,
                           auth=self.auth)
        res.raise_for_status()
        return res.json()

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

    def force_build(self, builderid, repo):
        """Force launch a build."""
        params = {
            'builderid': builderid,
            'username': '',
            'reason': 'force build',
            'repository': repo,
            'project': '',
            'branch': '',
            'revision': ''
        }
        self.post('forceschedulers/force-bootstrap', 'force', params=params)
