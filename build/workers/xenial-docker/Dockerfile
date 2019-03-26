FROM ubuntu:xenial

#
# Install packages needed by the buildchain
#
ARG DOCKER_VERSION=18.06.1~ce~3-0~ubuntu

COPY ./packages.list /tmp
RUN apt-get update \
    && cat /tmp/packages.list | xargs apt-get install -y \
    && rm -f /tmp/packages.list \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - \
    && echo "deb [arch=amd64] https://download.docker.com/linux/ubuntu xenial stable" \
      | tee -a /etc/apt/sources.list.d/docker-ce.list \
    && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
      docker-ce=${DOCKER_VERSION} \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /tmp

RUN pip3 install --no-binary buildbot --no-cache-dir -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

# Install helm
RUN curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get > \
 /tmp/get_helm.sh && bash /tmp/get_helm.sh

#
# Add user eve
#

RUN adduser -u 1042 --home /home/eve --disabled-password --gecos "" eve \
    && adduser eve sudo \
    && sed -ri 's/(%sudo.*)ALL$/\1NOPASSWD:ALL/' /etc/sudoers

#
# Eve configuration
#

USER eve

RUN mkdir -p /home/eve/workspace/ \
    && mkdir -p /home/eve/.ssh/ \
    && /bin/echo -e "Host bitbucket.org\n\tStrictHostKeyChecking no\n" >> /home/eve/.ssh/config

#
# Run buildbot-worker on startup
#
ARG BUILDBOT_VERSION
RUN sudo pip3 install buildbot-worker==$BUILDBOT_VERSION

WORKDIR /home/eve/workspace
CMD buildbot-worker create-worker . "$BUILDMASTER:$BUILDMASTER_PORT" "$WORKERNAME" "$WORKERPASS" \
    && buildbot-worker start --nodaemon
