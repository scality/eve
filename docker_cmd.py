#!/usr/bin/env python

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


print "Creating master..."
subprocess.check_call('buildbot create-master .', shell=True)

print "Upgrading master..."
subprocess.check_call('buildbot upgrade-master .', shell=True)

print "Starting master..."
try:
    subprocess.check_call('buildbot start .', shell=True)
except Exception:
    subprocess.check_call('tail -n 1000 twistd.log', shell=True)
    raise
subprocess.check_call('tail -fn 1000 twistd.log', shell=True)