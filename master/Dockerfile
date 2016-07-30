FROM ubuntu

EXPOSE :8000
EXPOSE :9000

# Install buildbot and its dependencies
RUN apt-get update -y
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python-pip \
    wget \
    python-dev \
    libssl-dev \
    libffi-dev \
    ca-certificates \
    libmysqlclient-dev \
    git

RUN wget --no-verbose --tries=3 --timeout=30 https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py pip==8.1.2
COPY requirements.txt requirements.txt
RUN /usr/local/bin/pip install -r requirements.txt

# Create buildbot folder
RUN buildbot create-master master


# Copy buildbot configuration
COPY master.cfg.py master/master.cfg

COPY certs master/certs
ENV DOCKER_CERT_PATH /master/certs/docker_workers
ENV GIT_KEY_PATH /root/.ssh/id_rsa

# Copy over private key and set permissions
RUN mkdir /root/.ssh/
RUN mv master/certs/git/id_rsa $GIT_KEY_PATH
RUN chmod 600 $GIT_KEY_PATH
RUN ls
RUN ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts 2> /dev/null

CMD buildbot create-master --relocatable -f --db=$DB_URL master; buildbot upgrade-master /master; buildbot start master;  tail -f master/twistd.log
