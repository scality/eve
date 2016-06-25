FROM ubuntu

ENV DOCKER_TLS_VERIFY 1
ENV DOCKER_CERT_PATH /master/docker_worker/docker_certs
ENV DOCKER_HOST tcp://buildfaster.devsca.com:2376

# Install buildbot and its dependencies
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python-pip \
    python-dev \
    libssl-dev \
    libffi-dev \
    git

RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt


# Make ssh dir
RUN mkdir /root/.ssh/

## Copy over private key for git
COPY docker_worker/git_certs/id_rsa /root/.ssh/id_rsa
RUN ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts

## COPY worker docker context and certificates
COPY docker_worker master/docker_worker

# Create buildbot folder
RUN buildbot create-master master

# Setup running docker container buildbot process
EXPOSE :8000
EXPOSE :9989

# Copy buildbot configuration
COPY master.cfg.py master/master.cfg

CMD buildbot start master; tail -f master/twistd.log