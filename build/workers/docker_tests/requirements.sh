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


# Install kubectl
curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | tee /etc/apt/sources.list.d/kubernetes.list
apt-get update && apt-get install -y kubectl

# Install Kind
curl -Lo ./kind https://github.com/kubernetes-sigs/kind/releases/download/v0.10.0/kind-linux-amd64
chmod +x ./kind
mv kind /usr/local/bin/
# Create kind cluster
kind create cluster
# Setup Kind kubeconfig
mkdir -p /home/eve/.kube
kind get kubeconfig > /home/eve/.kube/config
chown eve:eve /home/eve/.kube/config
