FROM ubuntu:trusty

RUN apt-get update && apt-get install -y \
   python-dev \
   python-pip \
   git

RUN pip install --upgrade pip
RUN pip install buildbot-worker==0.9.0b9
RUN groupadd -r buildbot && useradd -r -g buildbot buildbot
RUN mkdir /worker && chown buildbot:buildbot /worker

# Make ssh dir
RUN mkdir /root/.ssh/

# Copy over private key, and set permissions
COPY id_rsa /root/.ssh/id_rsa
RUN ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts

WORKDIR /worker
CMD  buildbot-worker create-worker . $BUILDMASTER $WORKERNAME $WORKERPASS && buildbot-worker start --nodaemon