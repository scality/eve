#!/bin/bash

master_fqdn=$1
master_port=$2
worker_name=$3
worker_password=$4

export LANG=en_US.utf8

sudo -iu eve buildbot-worker create-worker --umask=22 \
                             /home/eve/worker \
                             ${master_fqdn}:${master_port} \
                             ${worker_name} \
                             ${worker_password}

sudo -iu eve buildbot-worker start /home/eve/worker
