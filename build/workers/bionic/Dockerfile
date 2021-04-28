FROM ubuntu:focal

#
# Install packages needed by the buildchain
#

COPY ./packages.list /tmp
RUN apt-get update \
    && cat /tmp/packages.list | xargs apt-get install -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /tmp/packages.list

COPY ./requirements.txt /tmp

RUN pip3 install --upgrade pip==21.1
RUN pip3 install --no-binary buildbot --no-cache-dir -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

# Install Helm
ARG HELM_VERSION=3.5.4
RUN curl -sSL https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz | tar -xvz \
 && install linux-amd64/helm /usr/local/bin \
 && rm -rf linux-amd64
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
