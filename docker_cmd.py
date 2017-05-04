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

import sys
import time
import requests
import sqlalchemy
import subprocess

db_url = sys.argv[1]
wamp_router_url = sys.argv[2]

print 'pinging crossbar...{} ...'.format(wamp_router_url)

for i in xrange(120):
    try:
        requests.get(wamp_router_url.replace('ws://', 'http://'))
        break
    except requests.exceptions.ConnectionError:
        print('Waiting for the wamp queue to wake up {} ...'.format(
            wamp_router_url))
        time.sleep(1)
else:
    raise Exception('The wamp server never responded')

print 'pinging database...'
sa = sqlalchemy.create_engine(db_url.split('?')[0])

for i in xrange(120):
    try:
        sa.execute('select 1;')
        break
    except sqlalchemy.exc.OperationalError:
        print('Waiting for the database to wake up {} ...'.format(db_url))
        time.sleep(1)
else:
    raise Exception('The database never responded')

import os

if os.environ['MASTER_MODE'] == 'frontend':
    # Backends must start before frontends because builders need to be
    # available before launching the first build.
    # Failure to do so leads to build not triggered during the first 5 minutes
    # until the next sync.
    time.sleep(10)

print "Upgrading master..."
subprocess.check_call('buildbot upgrade-master .', shell=True)

print "Starting master..."
subprocess.check_call('twistd -ny ./buildbot.tac', shell=True)
