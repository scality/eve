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
"""Eve client allowing to launch builds without pushing code to git."""

from __future__ import print_function

import argparse

from buildbot.clients import tryclient
from twisted.python import log


def output(*msg):
    """Monkey patch allowing to print log to stdout in addtion to log file."""
    for msgline in msg:
        line = str(msgline)
        print(line)
        log.msg(line)


def run(host, port, passwd, wait):
    """Run eve client.

    Args:
        host (str): The eve host (e.g. example.com).
        port (int): The try port (e.g. 7999).
        passwd (str): The master try password.

    """
    tryclient.output = output
    config = dict(
        connect='pb',
        vc='git',
        username='try',
        passwd=passwd,
        master='%s:%s' % (host, port),
        wait=wait,
    )
    tryc = tryclient.Try(config)
    tryc.run()


def main():
    """Parse commandline and run eve client."""
    parser = argparse.ArgumentParser(description='Send diff to eve')
    parser.add_argument('--host', help='the eve master host name')
    parser.add_argument('--port', help='the eve master try port')
    parser.add_argument('--passwd', help='the eve master try passwd')
    parser.add_argument('--wait', action='store_true', help='wait for finish')
    args = parser.parse_args()
    run(host=args.host, port=args.port, passwd=args.passwd, wait=args.wait)


if __name__ == '__main__':
    main()
