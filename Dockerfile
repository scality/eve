FROM        ubuntu:xenial

RUN         apt-get update && \
            DEBIAN_FRONTEND=noninteractive apt-get -y install -q \
                build-essential \
                curl \
                git \
                libffi-dev \
                libmysqlclient-dev \
                libssl-dev \
                python-dev \
                python-pip \
                python-psycopg2 \
                vim.tiny && \
            rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN curl -sSL https://get.docker.com/ | sh

RUN git config --global url."http://gitcache/https/bitbucket.org/".insteadOf git@bitbucket.org: \
 && git config --global url."http://gitcache/https/github.com/".insteadOf git@github.com: \
 && git config --global url."http://gitcache/git/mock/".insteadOf git@mock: \
 && mkdir /root/eve

VOLUME /root/eve
WORKDIR /root/eve

# Freezing requirements
COPY requirements/base.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY . /opt/eve
RUN pip install /opt/eve

COPY eve/etc/master.cfg /root/eve
COPY buildbot.tac /root/eve
COPY docker_cmd.py /root/eve

CMD /root/eve/docker_cmd.py
