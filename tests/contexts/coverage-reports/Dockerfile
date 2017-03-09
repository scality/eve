FROM ubuntu:trusty

RUN locale-gen en_US.UTF-8 \
    && echo "LANG=en_US.UTF-8\nLC_ALL=en_US.UTF-8" > /etc/default/locale

ENV LANG=en_US.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    TERM=xterm

RUN apt-get update \
 && apt-get install -y \
      curl \
      python-dev \
      git \
 && rm -rf /var/lib/apt/list/*

ARG BUILDBOT_VERSION
RUN curl -sSf https://bootstrap.pypa.io/get-pip.py | python \
 && pip2 install buildbot-worker==${BUILDBOT_VERSION}

COPY ssh-config /home/root/.ssh/config

COPY reports /tmp/reports

WORKDIR /worker
CMD buildbot-worker create-worker . "$BUILDMASTER:$BUILDMASTER_PORT" "$WORKERNAME" "$WORKERPASS" \
 && buildbot-worker start --nodaemon
