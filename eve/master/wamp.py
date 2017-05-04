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

"""Module to configure eve connection to wamp mq."""

# HACK
# Avoid compatibility issue between buildbot and newer versions of autobahn
from autobahn.twisted.wamp import Service


def monkey_patch_discard_extra_args(func):
    """Monkey patch a function to ignore extraneous keyword arguments.

    For example without monkey patching:
        >>> def hello(name='nobody'):
        ...     print('Hello %s!' % name)

        >>> hello(name='you', extra='spam')
        Traceback (most recent call last):
            ...
        TypeError: hello() got an unexpected keyword argument 'extra'

    Then becomes:
        >>> @monkey_patch_discard_extra_args
        ... def hello(name='nobody'):
        ...     print('Hello %s!' % name)

        >>> hello(name='you', extra='spam')
        Hello you!

    """
    import inspect
    spec = inspect.getargspec(func)

    def wrap(*args, **kwargs):
        """Wrapper discarding extra kwargs."""
        filtered = {k: v for k, v in kwargs.iteritems() if k in spec.args}
        func(*args, **filtered)

    # Be a well behaved decorator
    wrap.__name__ = func.__name__
    wrap.__doc__ = func.__doc__
    wrap.__dict__.update(func.__dict__)
    return wrap


Service.__init__ = monkey_patch_discard_extra_args(Service.__init__)


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
