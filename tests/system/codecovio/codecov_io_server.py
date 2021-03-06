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
"""Mock ``codecov.io`` REST API HTTP server.

Content:

* `CodecovIOMockServer`: HTTP server to mock ``codecov.io`` upload service.

"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time

from urllib.parse import urlencode, urlparse, parse_qsl


class _RequestRec(object):
    """HTTP request received object."""

    ignore_headers = ('accept-encoding', 'host')
    """List of ignored HTTP headers."""

    def __init__(self, command, path, headers):
        """`_RequestRec` constructor.

        Args:
            command (str): HTTP verb (POST, PUT, DELETE, ...).
            path (str): URL path used.
            headers (dict): HTTP headers.

        """
        self.command = command.upper() if command else None
        path_parts = urlparse(path)
        self.path = path_parts.path
        self.query_params = dict(parse_qsl(path_parts.query))
        self.headers = {
            key.lower(): value
            for key, value in dict(headers).items()
            if key.lower() not in self.ignore_headers
        }

    @classmethod
    def from_request(cls, request):
        """Return `_RequestRec` instance from http request."""
        return cls(request.command, request.path, request.headers)

    @classmethod
    def from_args(cls, command, path, query_params=None, headers=None):
        """Return `_RequestRec` instance from given arguments."""
        if query_params:
            path = '{0}?{1}'.format(path, urlencode(query_params))
        return cls(command, path, headers)

    def __eq__(self, obj):
        """Compare with another `_RequestRec` instance.

        Args:
            obj (_RequestRec): other instance to compare to.

        Returns:
            bool: True if the given `_RequestRec` instance has the same
                properties, False otherwise.

        """
        return all([
            self.command == obj.command, self.path == obj.path,
            self.query_params == obj.query_params, self.headers == obj.headers
        ])

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def __repr_dict(values, indent=''):
        """Pretty display a given dict.

        Args:
            values (dict): Dict to display.
            indent (str): Prefix to print on each line.

        """
        result = ''
        for key in sorted(values.keys()):
            if result:
                result += ',\n{0}    '.format(indent)
            result += '{0!r}: {1!r}'.format(key, values[key])

        if result:
            result = '{{\n{0}    {1}\n{0}}}'.format(indent, result)
        else:
            result = '{}'

        return result

    def __repr__(self):
        """Representation of the `_RequestRec` instance."""
        return '{0} {1}\n  Query params: {2}\n  Headers: {3}'.format(
            self.command, self.path,
            self.__repr_dict(self.query_params, indent='  '),
            self.__repr_dict(self.headers, indent='  '))


class _CodecovIORequestHandler(BaseHTTPRequestHandler):
    """HTTP handler of `CodecovIOMockServer`."""

    def do_POST(self):
        """Handle POST requests.

        If */upload/v4* path wanted, we compute and return a fake
        ``codecov.io`` response.

        """
        url_parts = urlparse(self.path)

        if url_parts.path == '/upload/v4':
            self.send_response(200)

            self.send_header('Content-Type', 'text/plain')
            self.end_headers()

            params = dict(parse_qsl(url_parts.query))
            repository = params.get('slug', 'scality/fake_repository')
            commit = params.get('commit', '0' * 40)

            self.wfile.write(
                'https://fake.codecov.io/bitbucket/{0}/commit/{1}\n'.format(
                    repository, commit).encode('utf-8'))

            self.wfile.write('{0}/s3/fake_report.txt?{1}\n'.format(
                self.server.url,
                urlencode({
                    'AWSAccessKeyId': 'FAKEAWSACCESSKID',
                    'Expires': self.server.expires,
                    'Signature': 'FAKESIGNATURE',
                }), ).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        """Handle PUT requests.

        Returns:
            *200* HTTP status if the path wanted is */s3*, *404* otherwise.

        """
        url_parts = urlparse(self.path)

        if url_parts.path.startswith('/s3'):
            self.send_response(200)
        else:
            self.send_response(404)
        self.end_headers()

    def parse_request(self):
        """Parse all requests.

        Store the request received to verify the ``coecov.io`` handshake.

        """
        ret = BaseHTTPRequestHandler.parse_request(self)
        if ret:
            self.server.register_request_rec(self)
        return ret


class CodecovIOMockServer(HTTPServer):
    """Mock of ``codecov.io`` HTTP server.

    The goal of this HTTP server is to react like a real
    ``codecov.io`` server (see
    https://docs.codecov.io/v4.3.0/reference#upload).

    """

    def __init__(self, bind_address='localhost'):
        """`CodecovIOMockServer` constructor.

        Args:
            bind_address (str): Bind address of the TCP socket to use.

        """
        HTTPServer.__init__(self, (bind_address, 0),
                            _CodecovIORequestHandler)

        self._th = None

        self.expires = int(time.time()) + 10
        self.request_received_list = []

    def assert_request_received_with(self, *args):
        """Check all request received.

        Check if all request received is in accordance with the list
        of expected requests given.

        Raises:
            AssertionError: If a request differ.

        """
        for idx, expected_request_received_args in enumerate(args):
            expected_request_received = _RequestRec.from_args(
                *expected_request_received_args)

            if idx >= len(self.request_received_list):
                raise AssertionError(
                    'Expected received request: {0!r}\n'
                    'Not received'.format(expected_request_received))

            request_received = self.request_received_list[idx]
            if expected_request_received != request_received:
                raise AssertionError('Expected received request:\n  {0!r}\n'
                                     'Received:\n  {1!r}'.format(
                                         expected_request_received,
                                         request_received))

    def register_request_rec(self, request):
        """Register the given request on the stack.

        Args:
            request: Request to add in the stack.

        """
        request_rec = _RequestRec.from_request(request)
        self.request_received_list.append(request_rec)

    @property
    def url(self):
        """Return the URL of this HTTP server."""
        return 'http://localhost:{0}'.format(self.server_port)

    def start(self):
        """Start the HTTP server.

        Create a thread to listen the HTTP server in background.

        """
        assert self._th is None, 'Thread already started'

        self._th = threading.Thread(target=self.serve_forever)
        self._th.setDaemon(True)
        self._th.start()

    def stop(self):
        """Stop the HTTP server."""
        self.shutdown()

        if self._th:
            self._th.join()
            self._th = None
