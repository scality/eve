"""Module to configure eve connection to wamp mq."""


def get_wamp_conf(router_url, realm):
    """Generate a wamp config.

    Args:
        router_url (str): The complete URL to the wamp router.
        realm (str): The realm eve will use on this router.
    """
    return {
        'type': 'wamp',
        'router_url': router_url,
        'realm': realm.decode(),  # wamp wants a unicode string here
        'debug': True,
        'debug_websockets': False,
        'debug_lowlevel': False,
    }
