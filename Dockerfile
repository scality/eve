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

COPY requirements/base.txt requirements.txt
RUN pip install -r requirements.txt

RUN mkdir /root/eve
WORKDIR /root/eve

COPY . /opt/eve
RUN pip install /opt/eve

RUN cp /opt/eve/src/eve/etc/master.cfg .

RUN git config --global url."http://git_cache/bitbucket.org/".insteadOf git@bitbucket.org:
RUN git config --global url."http://git_cache/github.com/".insteadOf git@github.com:
RUN git config --global url."http://git_cache/mock/".insteadOf git@mock:

COPY docker_cmd.sh .
RUN chmod +x docker_cmd.sh

CMD exec ./docker_cmd.sh
