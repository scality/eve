FROM ubuntu

RUN mkdir /root/.ssh/
EXPOSE :8000
EXPOSE :9989

# Install buildbot and its dependencies
RUN apt-get update -y
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
COPY worker_docker_certs master/worker_docker_certs
ENV DOCKER_CERT_PATH /master/worker_docker_certs

# Create buildbot folder
RUN buildbot create-master master

# Copy buildbot configuration
COPY master.cfg.py master/master.cfg

CMD echo $GIT_CERT_KEY_BASE64 | base64 --decode > /root/.ssh/id_rsa \
         && chmod 600 /root/.ssh/id_rsa \
         && ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts \
         && buildbot start master ; tail -f master/twistd.log
