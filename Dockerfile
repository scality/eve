FROM        ubuntu:xenial
ARG         DEBIAN_FRONTEND=noninteractive

RUN         apt-get update && \
            apt-get -y upgrade && \
            apt-get -y install -q \
                build-essential \
                curl \
                python-dev \
                libffi-dev \
                libssl-dev \
                python-pip \
                libmysqlclient-dev \
                git \
                python-psycopg2 && \
            rm -rf /var/lib/apt/lists/*

# Install required python packages, and twisted
RUN pip install --upgrade pip setuptools

# Freezing requirements
COPY requirements/base.txt requirements.txt
RUN pip install -r requirements.txt

RUN curl -sSL https://get.docker.com/ | sh
RUN mkdir /root/eve
WORKDIR /root/eve

COPY . /opt/eve
RUN pip install /opt/eve

RUN cp /opt/eve/eve/etc/master.cfg .

RUN git config --global url."http://gitcache/https/bitbucket.org/".insteadOf git@bitbucket.org:
RUN git config --global url."http://gitcache/https/github.com/".insteadOf git@github.com:
RUN git config --global url."http://gitcache/git/mock/".insteadOf git@mock:

COPY docker_cmd.py .
RUN chmod +x docker_cmd.py

ENTRYPOINT ./docker_cmd.py $DB_URL $WAMP_ROUTER_URL
