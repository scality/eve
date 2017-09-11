FROM        ubuntu:xenial

RUN         apt-get update && \
            DEBIAN_FRONTEND=noninteractive apt-get -y install -q \
                build-essential \
                curl \
                git \
                libffi-dev \
                libmysqlclient-dev \
                libssl-dev \
                mysql-client \
                python-dev \
                python-pip \
                python-psycopg2 \
                telnet \
                vim.tiny && \
            rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

ARG INTERNAL_DOCKER
RUN if [ -n "$INTERNAL_DOCKER" ]; then curl -sSL https://get.docker.com/ | sh; fi

VOLUME /root/eve/workspace
WORKDIR /root/eve/workspace

# Freezing requirements
COPY requirements/base.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY . /opt/eve
RUN pip install /opt/eve

COPY eve/etc/master.cfg /root/eve
COPY buildbot.tac /root/eve
COPY docker_cmd.py /root/eve

CMD /root/eve/docker_cmd.py
