FROM ubuntu:focal

RUN apt-get update && apt-get install -y \
   python3-dev \
   python3-pip \
   wget \
   git

ARG BUILDBOT_VERSION
RUN pip3 install buildbot-worker==${BUILDBOT_VERSION}

RUN groupadd -r buildbot && useradd -r -g buildbot buildbot
RUN mkdir /worker && chown buildbot:buildbot /worker

# Make ssh dir and add bitbucket to known_hosts
RUN mkdir /root/.ssh/
RUN /bin/echo -e "Host bitbucket.org\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config

WORKDIR /worker
CMD buildbot-worker create-worker . "$BUILDMASTER:$BUILDMASTER_PORT" "$WORKERNAME" "$WORKERPASS" \
 && buildbot-worker start --nodaemon
