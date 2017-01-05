#!/bin/bash
# This script is executed on Eve slaves and installs the
# minimum software to allow the slave to connect to the
# master.
#
# - Openstack slaves: this init.sh script is deployed
#    and executed automatically by Eve
# - Docker slaves: the script must be called in the
#    Dockerfile
#
# The init script is reponsible for:
# - installing buildbot worker and required dependencies
# - configuring a user 'eve' and giving it access to sudo
# - installing git (for initial repo checkout)
#
# This file MUST NOT be used to source any other build
# dependency. All other provisionning MUST be sourced from
# the project main.yml file, within one or more build steps.
#
# Arguments:
#  1: buildbot version number

set -o xtrace -o errexit -o nounset -o pipefail

BUILDBOT_VERSION=${1:-0.9.2}

# install buildbot worker
apt-get update
apt-get install -y python-dev python-pip
pip install service_identity  # required by twisted
pip install buildbot-worker==${BUILDBOT_VERSION}

# configure user eve
adduser -u 1042 --home /home/eve --disabled-password --gecos "" eve
adduser eve sudo
echo "%sudo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# install git
apt-get install -y git
