FROM ubuntu

RUN mkdir /root/.ssh/
EXPOSE :8000
EXPOSE :9989

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

## COPY worker docker context and certificates
COPY docker_worker master/docker_worker
ENV DOCKER_CERT_PATH /master/docker_worker/docker_certs

# Create buildbot folder
RUN buildbot create-master master

# Copy buildbot configuration
COPY master.cfg.py master/master.cfg

CMD echo $GIT_CERT_KEY_BASE64 | base64 --decode > $HOME/.ssh/id_rsa \
         && chmod 600 $HOME/.ssh/id_rsa \
         && ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts \
         && buildbot start master ; tail -f master/twistd.log
