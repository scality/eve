#!/usr/bin/env python

"""A set of git hosts utilities, which handle authentication based on the
provider.

A factory function is available to provide a configured Provider instance for
any of the supported hosts. Depending on the instanciated provider, the kwargs
dict shall provide various parameters, as per the following documentation.

In order to use the authentication of the providers, please configure
your account using the method relevant for the concerned provider:

Bitbucket:
    Go to https://bitbucket.org/account/user/<your_username>/api
    and create a new consumer with the following settings:
    - details:
        - Callback URL: <eve base URL>
    - permissions:
        - account: READ access
        - team membership: READ access

    -> Specify the created consumer ids and secret as follow to the factory
       function:
         - client_id: <Generated consumer ID>
         - client_secret: <Generated consumer Secret>

Github:
    Go to https://github.com/settings/tokens
    and create a new token with the following settings:
    - description: eve-api-client
    - scopes: user (read:user, user:email and user:follow)

    -> Provide the newly created token as follows to the factory function:
         - token: <Generated token>


In addition to the factory function, this module also provides an
"interpolating" function, which attempts based on a "mode" (either `auto` or
anything else), to guess the provider required from the name or the url
provided.

In order to link up the whole thing, you can use the following code:
    githost = guessProvider('auto', None, 'http://github.com/scality/Zenko')
    provider = getProvider(githost, **authparams)

or alternatively:
    provider = getProvider('bitbucket', **authparams)

Report any bug/error at release.engineering@scality.com
"""

from abc import ABC, abstractmethod
import base64
import json
import sys
try:
    # python 3
    from urllib.request import Request, build_opener, HTTPError
except ImportError:
    # python 2
    from urllib2 import Request, build_opener, HTTPError


class BaseProvider(ABC):
    def __init__(self):
        self._token = None

    @property
    @abstractmethod
    def token(self):
        raise NotImplementedError


class BitBucketProvider(BaseProvider):
    def __init__(self, **kwargs):
        super().__init__()
        self._client_id = kwargs['client_id']
        self._client_secret = kwargs['client_secret']

        if self._client_secret is None or self._client_id is None:
            sys.exit(
                'The remote Git host is Bitbucket. Please provide a client '
                'id and client secret obtained from the OAuth page in '
                'https://bitbucket.org/account/user, via the --client-id '
                'and --client-secret options.'
            )

    @property
    def token(self):
        """Get an access token from Bitbucket OAuth API.

        Args (handled by the object):
            self._client_id (str): username of the client.
            self._client_secret (str): password of the client.

        Returns:
            string containing the access token

        """
        if not self._token:
            authstr = '{}:{}'.format(self._client_id, self._client_secret)
            base64auth = base64.b64encode(authstr.encode('ascii'))

            auth_url = 'https://bitbucket.org/site/oauth2/access_token'
            data = 'grant_type=client_credentials'.encode('ascii')
            req = Request(auth_url, data=data)
            req.get_method = lambda: 'POST'
            req.add_header("Authorization", "Basic %s" % base64auth.decode())
            try:
                res = build_opener().open(req)
            except HTTPError as excp:
                sys.exit('HTTP error: %s, %s (%s)' % (
                    excp.url, excp.reason, excp.code))

            res = res.read()
            self._token = json.loads(res.read().decode("utf-8"))['access_token']

        return self._token


class GitHubProvider(BaseProvider):
    def __init__(self, **kwargs):
        super().__init__()
        self._token = kwargs['token']
        if self._token is None:
            sys.exit(
                'The remote Git host is GitHub. Please provide a valid '
                'token obtained from https://github.com/settings/tokens, '
                'via the --token option.'
            )

    @property
    def token(self):
        return self._token


PROVIDERS = {
    'github': GitHubProvider,
    'bitbucket': BitBucketProvider,
}


def getProvider(name, **kwargs):
    """ Returns the instanciated BaseProvider object for the named provider

    Args:
        name (str): The name of the provider (see PROVIDERS constant's keys)
        kwargs (kwargs): The dict of possible authentication parameters. The
                         keys should match the required parameters for the
                         given Provider.

    Returns:
        provider (BaseProvider child object): The Provider instance to use
    """
    if name.lower() not in PROVIDERS.keys():
        raise Exception('No such git provider')

    return PROVIDERS[name.lower()](**kwargs)


def guessProvider(mode, name, baseurl):
    """ Returns the name of the Provider, based on the parameters values

    Args:
        mode (str): 'auto' to guess from the url, any other value to check from
                    the name parameter.
        name (str): name of the provider to double-check, if mode is not 'auto'
        baseurl (str): baseurl of the service to extract the Provider name
                       from, if the mode is 'auto'


    Returns:
        name (str): The valid name of the provider
    """
    if mode == 'auto':
        if 'github' in baseurl:
            return 'github'
        elif 'bitbucket' in baseurl:
            return 'bitbucket'
    if name in PROVIDERS.keys():
        return name
    sys.exit('cannot extrapolate githost from service URL or arguments'
             ', please specify it with -g/--githost option')
