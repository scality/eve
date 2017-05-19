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


print('pinging crossbar...')
wamp_router_url =  os.environ['WAMP_ROUTER_URL']
for i in xrange(120):
    try:
        requests.get(wamp_router_url.replace('ws://', 'http://'))
        break
    except requests.exceptions.ConnectionError:
        print('Waiting for the wamp queue to wake up {} ...'.format(
            wamp_router_url))
        time.sleep(1)
else:
    raise Exception('wamp server never responded')

print('pinging database...')
db_url = os.environ['DB_URL']
sa = sqlalchemy.create_engine(db_url.split('?')[0])
for i in xrange(120):
    try:
        sa.execute('select 1;')
        break
    except sqlalchemy.exc.OperationalError:
        print('Waiting for the database to wake up {} ...'.format(db_url))
        time.sleep(1)
else:
    raise Exception('database never responded')

print('upgrading master...')
subprocess.check_call('buildbot upgrade-master .', shell=True)

print('starting master...')
subprocess.check_call('twistd -ny ./buildbot.tac', shell=True)
