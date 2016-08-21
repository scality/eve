"""eve client allowing to launch builds without pushing code to git"""
from __future__ import print_function

import argparse

from buildbot.clients import tryclient
from twisted.python import log


def output(*msg):
    """Monkey patch allowing to print log to stdout in addtion to log file"""
    for msgline in msg:
        line = str(msgline)
        print(line)
        log.msg(line)


def run(host, port, passwd):
    """
    Run eve client
    :param host: e.g. example.com
    :param port: e.g. 7999
    :param passwd: the master try password
    :return: None
    """
    tryclient.output = output
    config = dict(
        connect='pb',
        vc='git',
        username='try',
        passwd=passwd,
        master='%s:%s' % (host, port),
        wait=True,
    )
    tryc = tryclient.Try(config)
    tryc.run()


def main():
    """main"""
    parser = argparse.ArgumentParser(description='Send diff to eve')
    parser.add_argument('--host', help='the eve master host name')
    parser.add_argument('--port', help='the eve master try port')
    parser.add_argument('--passwd', help='the eve master try passwd')
    args = parser.parse_args()
    run(host=args.host, port=args.port, passwd=args.passwd)


if __name__ == '__main__':
    main()
