from os import environ

from wamp import get_wamp_conf


def setup_multimaster(conf):
    wamp_router_url = environ.pop('WAMP_ROUTER_URL')
    wamp_realm = environ.pop('WAMP_REALM')
    conf['multiMaster'] = True
    conf['mq'] = get_wamp_conf(wamp_router_url, wamp_realm)
