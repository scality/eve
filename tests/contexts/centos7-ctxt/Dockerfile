FROM centos:7

RUN yum install -y epel-release

RUN yum -y install -y \
   python-devel \
   python-pip \
   wget \
   gcc \
   git

RUN wget --no-verbose --tries=3 --timeout=30 https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py pip==8.1.2
RUN /usr/bin/pip install buildbot-worker==0.9.0b9
RUN groupadd -r buildbot && useradd -r -g buildbot buildbot
RUN mkdir /worker && chown buildbot:buildbot /worker

# Make ssh dir
RUN mkdir /root/.ssh/

# Copy over private key, and set permissions
COPY id_rsa /root/.ssh/id_rsa
COPY id_rsa.pub /root/.ssh/id_rsa.pub
RUN ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts

# install docker
RUN yum install -y docker && groupadd docker && usermod root -aG docker

WORKDIR /worker
CMD  buildbot-worker create-worker . "$BUILDMASTER:$BUILDMASTER_PORT" "$WORKERNAME" "$WORKERPASS" && buildbot-worker start --nodaemon