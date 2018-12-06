#!/usr/bin/env python3.6

"""Access Eve/buildbot API from python code
"""

import logging
import json
import math
import parse
import sys
try:
    # python 3
    from http.cookiejar import CookieJar
    from urllib.request import (Request, build_opener, HTTPError,
                                HTTPCookieProcessor)
except ImportError:
    # python 2
    from cookielib import CookieJar


def extract_build_desc(base_url, url):
    fmt = '{}#builders/{{builder_id}}/builds/{{build_id}}'.format(base_url)
    res = parse.parse(fmt, url)
    return {'builder_id': res['builder_id'], 'build_id': res['build_id']}


class EveClient:
    """Handle Authentication and request formatting for Buildbot/Eve services

        The authentication is handled with a Cookie cache, so that the minimum
        number of requests is made towards the authentication endpoint of the
        sevice; reducing the number of round-trips when multiple requests are
        made to the service.
    """
    def __init__(self, auth_token, base_url):
        self._token = auth_token
        self._burl = base_url

        # These object attributes are used to allow authentifying only once for
        # the whole lifetime of the object.
        self._cookie_processor = HTTPCookieProcessor(CookieJar())
        self._authentified = False

    def _authenticate(self):
        """
            Authentifies once (and only once) the EveClient object with the
            actual Buildbot/Eve instance, and uses the object's internal
            cookies to make it usable for subsequent HTTP requests.
        """
        if self._authentified is True:
            return

        opener = build_opener(self._cookie_processor)

        auth_url = '{}/auth/login?token={}'.format(self._burl, self._token)
        auth_req = Request(auth_url)
        try:
            opener.open(auth_req)
        except HTTPError as excp:
            sys.exit('HTTP error: %s (%s) (check consumer permissions)' % (
                excp.reason, excp.code))

    def _request(self, httpmethod, path, payload={}, version=2):
        """Access buildbot API thank to pre-obtained access token.

        Object attributes and methods:
            self._token (str): OAuth2 access token
            self._burl (str): url of Eve/Buildbot instance
            self._authenticate() (method): ensure that the object is properly
                                           authentified with the Buildbot/Eve
                                           service

        Args:
            httpmethod (str): get/post/put/delete
            path (str): URI path to query
            payload (dict): The parameters to send to jsonrpc
            version: version of api to hit

        Returns:
            API response (json)

        """
        self._authenticate()

        data = json.dumps({
            'id': 999,
            # sequence number doesn't matter for synchronous requests
            'jsonrpc': '2.0',
            'method': 'force',
            'params': payload,
        }).encode('ascii')
        if path.startswith('/'):
            endpoint = path[1:]
        url = '{}/api/v{}/{}'.format(self._burl, version, endpoint)

        req = Request(url, data=data)
        req.add_header('Content-Type', 'application/json')
        req.get_method = lambda: httpmethod.upper()

        opener = build_opener(self._cookie_processor)
        try:
            res = opener.open(req)
        except HTTPError as excp:
            sys.exit('HTTP error: %s (%s)' % (excp.reason, excp.code))
        return json.load(res)

    def builders(self):
        return self._request('GET', '/builders')['builders']

    def getBootstrapId(self):
        builders = self.builders()
        launchers = [e for e in builders if e['name'] == 'bootstrap']
        assert(len(launchers) == 1)
        builder = launchers[0]
        return builder['builderid']

    def build(self, builder_id, build_id):
        url = '/builders/{}/builds/{}'.format(builder_id, build_id)
        return self._request('GET', url)

    def steps(self, builder_id, build_id, step=None):
        url = '/builders/{}/builds/{}/steps'.format(builder_id, build_id)
        if step:
            url += '/{}'.format(step)
        return self._request('GET', url)

    @staticmethod
    def _collect_urls(steps, depth=0):
        build_urls = []
        artifact_urls = []
        for step in steps['steps']:
            names = []
            # XXX NOTE FIXME : here, we will need to change the references and
            # usage when (and if) we switch to virtual builders, since the data
            # might look quite different after that.
            if 'state_string' in step and 'triggered' in step['state_string']:
                names = step['state_string'][len('triggered '):].split(', ')
            for idx in range(len(step['urls'])):
                url = step['urls'][idx]['url']
                logging.debug('{}Checking URL {}'.format(depth * 4 * ' ', url))
                if '/#builders/' in url and '/builds/' in url:
                    # Each stage generates a builds request + a build URL
                    # As such, we need to infer the index of the name from the
                    # index of the build link, which is part of the second half
                    # of the links.
                    # ex: the step triggers 4 stages.
                    # - len(names) ought to be 4
                    # - len(step['urls']) ought to be 8, composed of 4
                    #   buildrequest links, followed by 4 build links.
                    # - The build links with thus be located at index [4-7]
                    # - Thus, buildrequest at index 1 matches build link at
                    #   index 5, which matches the stage name at index 1
                    namei = math.floor(idx - len(step['urls']) / 2)
                    build_urls.append((names[namei], step['number'], idx, url))
                elif 'artifacts' in url:
                    artifact_urls.append(url)
                else:
                    logging.debug('{}Ignoring...'.format(depth * 4 * ' '))
        return (build_urls, artifact_urls)

    def buildtree(self, builder_id, build_id, depth=0):
        steps = self.steps(builder_id, build_id)
        builds = {}
        build_urls, artifact_urls = self._collect_urls(steps, depth)
        for (stage_name, stepidx, idx, url) in build_urls:
            step = steps['steps'][stepidx]
            desc = extract_build_desc(self._burl, url)
            sub_build = self.buildtree(depth=depth + 1, **desc)
            builds[url] = {
                'step': step['name'],
                'stage': stage_name,
                'stepid': step['stepid'],
                'desc': desc,
                'builds': sub_build['builds'],
                'artifacts': sub_build['artifacts'],
            }
        return {'builds': builds, 'artifacts': artifact_urls}
