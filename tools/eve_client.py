
import json
import sys
try:
    # python 3
    from http.cookiejar import CookieJar
    from urllib.request import (Request, build_opener, HTTPError,
                                HTTPCookieProcessor)
except ImportError:
    # python 2
    from cookielib import CookieJar


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
