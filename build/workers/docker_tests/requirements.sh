#!/bin/bash

set -o xtrace -o errexit -o nounset -o pipefail


# Configure docker repository
apt-get update
apt-get install -y apt-transport-https

echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main" \
    > /etc/apt/sources.list.d/docker.list
apt-key adv \
    --keyserver hkp://p80.pool.sks-keyservers.net:80 \
    --recv-keys 58118E89F3A912897C070ADBF76221572C52609D



# install docker
apt-get update
apt-get install -y docker-engine
adduser eve docker

# Switch to overlay2 for docker
systemctl stop docker.service
rm -rf /var/lib/docker
cat << EOF > /etc/docker/daemon.json
{
    "storage-driver": "overlay2"
}
EOF
systemctl start docker.service



# install test requirements
apt-get install -y \
         ca-certificates \
         libffi-dev \
         libmysqlclient-dev \
         libssl-dev \
         python-dev \
         python-pip

pip install --upgrade pip
pip install tox==2.3.2
