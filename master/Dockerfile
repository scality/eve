FROM ubuntu

EXPOSE :8000
EXPOSE :9000

# Install buildbot and its dependencies
RUN apt-get update -y
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python-pip \
    wget \
    python-dev \
    libssl-dev \
    libffi-dev \
    ca-certificates \
    libmysqlclient-dev \
    git

RUN wget --no-verbose --tries=3 --timeout=30 https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py pip==8.1.2
COPY requirements.txt requirements.txt
RUN /usr/local/bin/pip install -r requirements.txt

# copy docker credentials/certificates
COPY certs /certs
ENV DOCKER_CERT_PATH /certs/docker_workers

# Copy over private key for git and set permissions
ENV GIT_KEY_PATH /root/.ssh/id_rsa
RUN mkdir /root/.ssh/
RUN mv /certs/git/id_rsa $GIT_KEY_PATH
RUN chmod 600 $GIT_KEY_PATH
RUN ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts 2> /dev/null

# Create buildbot folder
RUN mkdir master

# Copy buildbot configuration
COPY master.cfg.py master/master.cfg

CMD buildbot create-master --quiet --relocatable --db=$DB_URL master; buildbot start master;  tail -f master/twistd.log
