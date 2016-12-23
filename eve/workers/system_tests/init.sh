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

BUILDBOT_VERSION=${1:-0.9.0.post1}

# install buildbot worker
for i in $(seq 1 10); do
    if apt-get update && apt-get install -y \
        apt-transport-https \
        ca-certificates \
        libffi-dev \
        libssl-dev \
        python-dev \
        python-pip; then
        break
    else
        echo "Installing packages failed ${i}nth time"
        echo "Retrying"
        sleep 5
    fi
done

pip install service_identity  # required by twisted
pip install twisted==16.4.0
pip install buildbot-worker=="${BUILDBOT_VERSION}"

# Configure docker repository
echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main" \
    > /etc/apt/sources.list.d/docker.list
apt-key adv \
    --keyserver hkp://p80.pool.sks-keyservers.net:80 \
    --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

# install git and docker
apt-get update
apt-get install -y git docker-engine

# configure user eve
adduser -u 1042 --home /home/eve --disabled-password --gecos "" eve
adduser eve sudo
adduser eve docker
echo "%sudo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers


# Switch to overlay2 for docker
systemctl stop docker.service
rm -rf /var/lib/docker
cat << EOF > /etc/docker/daemon.json
{
    "storage-driver": "overlay2"
}
EOF
systemctl start docker.service

mkdir -p /home/eve/.ssh/ && /bin/echo -e "Host *\n\tStrictHostKeyChecking no\n" >> /home/eve/.ssh/config
