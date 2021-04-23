# Copyright 2018 Scality
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

from hashlib import md5, sha1


def create_hash(*args):
    """Return a unique name based on args.

    The value must be useable as a valid namespace name
    and a valid UUID for service providers. In the case
    of GCE service accounts for example, this means less
    than 30 chars, and start with a letter.

    We return the md5 sum of the provided args, make sure
    the first character is an 'e' for Eve, and limit the md5
    signature to 28 characters, which will hopefully be enough
    to avoid collisions.

    """
    m = md5()
    for arg in args:
        m.update(str(arg).encode())
    return "e%s" % m.hexdigest()[:28]


def hash_dict(dict_obj):
    """Create a sha1 hash of a dict and return it."""
    if not isinstance(dict_obj, dict):
        raise ValueError('Parameter is not of type dict')
    args_sha1 = sha1()
    for key in sorted(dict_obj.keys()):
        args_sha1.update((key + str(dict_obj[key])).encode('utf-8'))
    return args_sha1
