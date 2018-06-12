#!/usr/bin/env python

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

from __future__ import print_function

import os
import subprocess
import sys
import time

import requests
import sqlalchemy

def _print(string):
    """Print and flush for immediate display."""
    print(string)
    sys.stdout.flush()

wamp_router_url = os.environ.get('WAMP_ROUTER_URL', '')
if wamp_router_url:
    _print("pinging crossbar...")
    for i in xrange(120):
        try:
            requests.get(wamp_router_url.replace('ws://', 'http://'))
            break
        except requests.exceptions.ConnectionError:
            _print('Waiting for the wamp queue to wake up {} ...'.format(
                wamp_router_url))
            time.sleep(1)
    else:
        raise Exception('wamp server never responded')

_print("pinging database...")
db_url = os.environ['DB_URL']
sa = sqlalchemy.create_engine(db_url.split('?')[0])
for i in xrange(120):
    try:
        sa.execute('select 1;')
        break
    except sqlalchemy.exc.OperationalError:
        _print('Waiting for the database to wake up {} ...'.format(db_url))
        time.sleep(1)
else:
    raise Exception('database never responded')

_print("checking cloud key mode...")
openstack_key =  os.environ.get('OS_SSH_KEY', False)

if os.environ.get('DEBUG_MODE', '0') in ['true', 'True', '1', 'y', 'yes']:
    _print("starting in debug mode...")
    _print("-> to start buildbot manually, connect to container then type:")
    _print("   $ twistd -ny ./buildbot.tac")
    _print("-> to connect to interactive session, type:")
    _print("   $ telnet 127.0.0.1 12345")
    _print("-> to resume normal startup sequence, type:")
    _print("   $ pkill -f tail")

    try:
        subprocess.check_call('tail -f /dev/null', shell=True)
    except:
        pass
    _print("resuming startup sequence")

if os.environ.get('MASTER_MODE', 'standalone') in ['frontend', 'standalone']:
    _print("upgrading master...")
    subprocess.check_call('buildbot upgrade-master .', shell=True)

_print("starting master...")
subprocess.check_call('twistd -ny ./buildbot.tac', shell=True)
