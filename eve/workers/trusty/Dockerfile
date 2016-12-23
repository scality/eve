FROM ubuntu:trusty

#
# Add user eve
#

RUN adduser -u 1042 --home /home/eve --disabled-password --gecos "" eve \
    && adduser eve sudo \
    && sed -ri 's/(%sudo.*)ALL$/\1NOPASSWD:ALL/' /etc/sudoers

WORKDIR /home/eve

#
# Install packages needed by the buildchain
#

COPY ./packages.list /tmp
RUN apt-get update \
    && cat /tmp/packages.list | xargs apt-get install -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /tmp/packages.list

COPY ./requirements.txt /tmp
RUN pip2 install -U pip==8.1.2 \
    && pip2 install -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

#
# Eve configuration
#

USER eve

RUN mkdir -p /home/eve/.ssh/ \
    && /bin/echo -e "Host bitbucket.org\n\tStrictHostKeyChecking no\n" >> /home/eve/.ssh/config 

#
# Run buildbot-worker on startup
#

CMD buildbot-worker create-worker . "$BUILDMASTER:$BUILDMASTER_PORT" "$WORKERNAME" "$WORKERPASS" \
    && buildbot-worker start --nodaemon
