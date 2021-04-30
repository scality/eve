#!/bin/bash

exec 3>&1 4>&2 >/var/log/custom_cloud_init_output.log 2>&1

worker_version=$1
python_pip_cmd=pip

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

  retry yum -y install glibc-locale-source redhat-lsb-core
  dist_major=$(lsb_release -sr | cut -d . -f 1)

  retry yum -y install git gcc libffi-devel openssl-devel

  if [ "$dist_major" == "8" ]; then
    retry dnf -y install python2-devel python2-setuptools
  else
    retry yum -y install python-devel python-setuptools
  fi

  adduser -u 1042 --home-dir /home/eve eve
  usermod -G wheel eve
  echo "%wheel ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
  if [ "$(rpm -q --queryformat '%{VERSION}' centos-release)" = "6" ]
  then
    twisted_version=15.4 # no more recent with python2.6 (Centos 6 only)
    # buildbot > 0.9.12 requires a version of twisted that is not supported
    # by python2.6
    worker_version=0.9.12
    python_version=2.6
  else
    twisted_version=16.4.0
    python_version=2.7
  fi

  curl https://bootstrap.pypa.io/pip/${python_version}/get-pip.py -o get-pip.py
  python get-pip.py pip==9.0.3

elif [ -f /etc/debian_version ]
then
  echo "Ubuntu/Debian"

  retry apt-get update

  locale-gen en_US.UTF-8
  export LANG=en_US.utf8

  export DEBIAN_FRONTEND=noninteractive

  if [[ `lsb_release -sc` =~ ^(focal)$ ]];
  then
    python_pip_package=python3-pip
    python_pip_cmd=pip3
    twisted_version=20.3.0
  else
    python_pip_package=python-pip
    python_pip_cmd=pip
    twisted_version=16.4.0
  fi
  retry apt-get install --yes git gcc python-dev python-setuptools libffi-dev ${python_pip_package}

  adduser -u 1042 --home /home/eve --disabled-password --gecos "" eve
  adduser eve sudo
  echo "%sudo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
  if [[ `lsb_release -sc` =~ ^(precise|wheezy)$ ]];
  then
    worker_version=1.7.0 # last version of buildbot with python2.7 support
  fi
else
  echo "Unsupported Operating System";
  exit 1;
fi

# install twisted and buildbot
retry sudo ${python_pip_cmd} install --index-url=https://pypi.python.org/simple/ --upgrade pip==9.0.3
retry sudo ${python_pip_cmd} install twisted==$twisted_version
retry sudo ${python_pip_cmd} install buildbot-worker==$worker_version
