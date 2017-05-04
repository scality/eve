# coding: utf-8

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

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Hack to remove a lot of warnings in stdout while testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class BuildbotDataAPI(object):
    """Class to interact with a Buildbot master through its REST API."""

    def __init__(self, uri):
        self.uri = uri
        self.api_uri = "{0}api/v2/".format(self.uri)

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
            'id': 1,  # sequence number doesn't matter for synchronous requests
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }

        res = self.session.post(self.api_uri + route, json=data)
        res.raise_for_status()
        return res.json()

    def get(self, route):
        """Get data from the REST API."""
        res = self.session.get(self.api_uri + route, headers={
            "Accept": "application/json"
        })
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
