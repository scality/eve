FROM ubuntu:xenial

RUN apt-get update && apt-get install -y \
   python-dev \
   python-pip \
   wget \
   git

RUN wget --no-verbose --tries=3 --timeout=30 https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py pip==8.1.2

ARG BUILDBOT_VERSION
RUN /usr/local/bin/pip install buildbot-worker==${BUILDBOT_VERSION}

RUN groupadd -r buildbot && useradd -r -g buildbot buildbot
RUN mkdir /worker && chown buildbot:buildbot /worker

# Make ssh dir and add bitbucket to known_hosts
RUN mkdir /root/.ssh/
RUN /bin/echo -e "Host bitbucket.org\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config

RUN wget -qO- https://get.docker.com/ | sh
WORKDIR /worker
CMD buildbot-worker create-worker . "$BUILDMASTER:$BUILDMASTER_PORT" "$WORKERNAME" "$WORKERPASS" \
 && buildbot-worker start --nodaemon
