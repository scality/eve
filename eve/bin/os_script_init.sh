#!/bin/bash

worker_version=$1

function retry {
  local n=1
  local max=5
  local delay=30
  echo "Running this command with retry ($max attempts, $delay seconds delay):"
  echo "'$@'"
  while true; do
  echo "Attempt $n/$max:"
  "$@" && break || {
    if [[ $n -lt $max ]]; then
      ((n++))
      echo "Command failed. Sleeping $delay seconds." >&2
      sleep $delay;
    else
      echo "The command has failed after $n attempts." >&2
      exit 1
    fi
  }
  done
  echo "The command has succeeded."
}

# configure user eve and twisted version
if [ -f /etc/redhat-release ]
then
  echo "CentOS/RedHat";

  localedef -v -c -i en_US -f UTF-8 en_US.UTF-8 || true
  export LANG=en_US.utf8

  retry yum -y install git gcc python-devel python-setuptools libffi-devel openssl-devel
  retry easy_install pip==9.0.3

  adduser -u 1042 --home-dir /home/eve eve
  usermod -G wheel eve
  echo "%wheel ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
  if [ "$(rpm -q --queryformat '%{VERSION}' centos-release)" = "6" ]
  then
    twisted_version=15.4 # no more recent with python2.6 (Centos 6 only)
  else
    twisted_version=16.4.0
  fi
elif [ -f /etc/debian_version ]
then
  echo "Ubuntu/Debian"

  retry apt-get update

  locale-gen en_US.UTF-8
  export LANG=en_US.utf8

  retry apt-get install --yes git gcc python-dev python-setuptools libffi-dev python-pip

  adduser -u 1042 --home /home/eve --disabled-password --gecos "" eve
  adduser eve sudo
  echo "%sudo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
  twisted_version=16.4.0
else
  echo "Unsupported Operating System";
  exit 1;
fi

# install twisted and buildbot
retry sudo pip install --index-url=https://pypi.python.org/simple/ --upgrade pip==9.0.3
retry sudo pip install twisted==$twisted_version
retry sudo pip install buildbot-worker==$worker_version
