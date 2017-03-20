from os import environ

from autobahn.twisted.wamp import Service
from buildbot.plugins import util

from ..bugfixes.wamp import monkey_patch_discard_extra_args


def setup_multimaster(conf):
    wamp_router_url = environ.pop('WAMP_ROUTER_URL')
    wamp_realm = environ.pop('WAMP_REALM')
    conf['multiMaster'] = True
    conf['mq'] = util.get_wamp_conf(wamp_router_url, wamp_realm)

    Service.__init__ = monkey_patch_discard_extra_args(Service.__init__)
