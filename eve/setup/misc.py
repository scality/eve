import time
from os import path

from buildbot import version
from buildbot.plugins import util


def register_starttime():
    util.env['MASTER_START_TIME'] = str(time.time())


def wamp():
    return {
        'type': 'wamp',
        'router_url': util.env.WAMP_ROUTER_URL,
        'realm': util.env.WAMP_REALM.decode(),
        'debug': True,
        'debug_websockets': False,
        'debug_lowlevel': False,
    }


def protocols():
    return {
        'pb': {
            'port': 'tcp:%s:interface=%s' % (util.env.PB_PORT, '0.0.0.0')
        }
    }


def verify_docker_certificates():
    """Checking that docker env vars are coherent."""
    if not util.env.DOCKER_TLS_VERIFY:
        return

    assert path.isfile(path.join(util.env.DOCKER_CERT_PATH, 'ca.pem'))
    assert path.isfile(path.join(util.env.DOCKER_CERT_PATH, 'key.pem'))
    assert path.isfile(path.join(util.env.DOCKER_CERT_PATH, 'cert.pem'))


def properties():
    return {
        'buildbot_version': version
    }
