#!/bin/bash

set -o xtrace -o errexit -o nounset -o pipefail

# Configure docker repository
apt-get update
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

# install docker
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io
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
         libffi-dev \
         libmysqlclient-dev \
         libssl-dev \
         python3-dev \
         python3-pip

pip3 install pip==9.0.1
pip3 install tox==2.3.2

# # install tooling for kubernetes tests
# wget https://storage.googleapis.com/kubernetes-release/release/v1.9.6/bin/linux/amd64/kubectl
# chmod +x ./kubectl
# mv ./kubectl /usr/local/bin/kubectl
# curl -Lo minikube https://storage.googleapis.com/minikube/releases/v0.25.2/minikube-linux-amd64
# chmod +x minikube
# mv minikube /usr/local/bin/

# HOME=/ minikube start --vm-driver none
# chmod 777 -R /.minikube /.kube
# ln -s /.minikube /.kube/.minikube
# ln -s /.kube /home/eve/.kube
