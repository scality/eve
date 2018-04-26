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

import time
from os import path

from buildbot import version
from buildbot.plugins import util
from pkg_resources import get_distribution


def register_starttime():
    util.env['MASTER_START_TIME'] = str(time.time())


def wamp():
    return {
        'type': 'wamp',
        'router_url': util.env.WAMP_ROUTER_URL,
        'realm': util.env.WAMP_REALM.decode(),
    }


def protocols():
    return {
        'pb': {
            'port': 'tcp:%s:interface=%s' % (util.env.PB_PORT, '0.0.0.0')
        }
    }


def verify_docker_certificates():
    """Check that docker env vars are coherent."""
    if not util.env.DOCKER_TLS_VERIFY:
        return

    assert path.isfile(path.join(util.env.DOCKER_CERT_PATH, 'ca.pem'))
    assert path.isfile(path.join(util.env.DOCKER_CERT_PATH, 'key.pem'))
    assert path.isfile(path.join(util.env.DOCKER_CERT_PATH, 'cert.pem'))


def properties():
    return {'buildbot_version': version}


def title():
    try:
        version = get_distribution('eve').version
    except Exception:
        version = 'unset_version'

    return "Eve (%s) project %s/%s/%s" % (
        version,
        util.env.GIT_HOST,
        util.env.GIT_OWNER,
        util.env.GIT_SLUG)
