# Copyright 2021 Scality
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

import buildbot
import requests
from buildbot.www import resource
from buildbot.www.oauth2 import GitHubAuth, OAuth2Auth, OAuth2LoginResource
from twisted.internet import defer, threads


@defer.inlineCallbacks
def renderLogin(self, request):
    code = request.args.get(b"code", [b""])[0]
    token = request.args.get(b"token", [b""])[0]
    if not token and not code:
        url = request.args.get(b"redirect", [None])[0]
        url = yield self.auth.getLoginURL(url)
        raise resource.Redirect(url)

    if not token:
        details = yield self.auth.verifyCode(code)
    else:
        details = yield self.auth.acceptToken(token)
    if self.auth.userInfoProvider is not None:
        infos = yield self.auth.userInfoProvider.getUserInfo(
            details['username']
        )
        details.update(infos)
    session = request.getSession()
    session.user_info = details
    session.updateSession(request)
    state = request.args.get(b"state", [b""])[0]
    if state:
        # pylint: disable=E0602
        for redirect in parse_qs(state).get('redirect', []):  # noqa: F821
            raise resource.Redirect(self.auth.homeUri + "#" + redirect)
    raise resource.Redirect(self.auth.homeUri)


def acceptToken(self, token):
    def thd():
        session = self.createSessionFromToken({'access_token': token})
        return self.getUserInfoFromOAuthClient(session)
    return threads.deferToThread(thd)


def createSessionFromToken(self, token):
    s = requests.Session()
    s.headers = {
        'Authorization': 'token ' + token['access_token'].decode('utf-8'),
        'User-Agent': 'buildbot/{}'.format(buildbot.version),
    }
    s.verify = self.sslVerify
    return s


def patch():
    """Patch created to restablish API authentication with OAuth enabled."""
    OAuth2LoginResource.renderLogin = renderLogin
    OAuth2Auth.acceptToken = acceptToken
    GitHubAuth.createSessionFromToken = createSessionFromToken
