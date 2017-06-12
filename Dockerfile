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

RUN pip install --upgrade pip

RUN curl -sSL https://get.docker.com/ | sh

RUN mkdir /root/eve /root/gitconfig \
 && touch /root/gitconfig/gitconfig \
 && ln -s /root/gitconfig/gitconfig /root/.gitconfig

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
