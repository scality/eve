
# HACK
# Avoid compatibility issue between buildbot and newer versions of autobahn
from autobahn.twisted.wamp import Service


def monkey_patch_discard_extra_args(f):
    import inspect
    spec = inspect.getargspec(f)

    def wrap(*args, **kwargs):
        filtered = {k: v for k, v in kwargs.iteritems() if k in spec.args}
        f(*args, **filtered)
    return wrap


Service.__init__ = monkey_patch_discard_extra_args(Service.__init__)


def get_wamp_conf(router_url, realm):
    return {
        'type': 'wamp',
        'router_url': router_url,
        'realm': realm.decode(),  # wamp wants a unicode string here
        'debug': True,
        'debug_websockets': False,
        'debug_lowlevel': False,
    }
