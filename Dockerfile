FROM ubuntu:xenial

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install -q \
        apt-transport-https \
        build-essential \
        curl \
        git \
        libffi-dev \
        libmysqlclient-dev \
        libssl-dev \
        lsof \
        mysql-client \
        python3-dev \
        python3-pip \
        python3-psycopg2 \
        python \
        python-requests \
        telnet \
        vim.tiny && \
    rm -rf /var/lib/apt/lists/*

# Install git lfs
RUN echo "deb https://packagecloud.io/github/git-lfs/ubuntu/ xenial main" > /etc/apt/sources.list.d/github_git-lfs.list && \
    curl -sSL https://packagecloud.io/github/git-lfs/gpgkey | apt-key add - && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install -q git-lfs && \
    git lfs install --system --skip-smudge --skip-repo

ARG INTERNAL_DOCKER
RUN if [ -n "$INTERNAL_DOCKER" ]; then curl -sSL https://get.docker.com/ | sh; fi

WORKDIR /root/eve

# Freezing requirements
COPY requirements/build.txt /tmp/build.txt
RUN pip3 install -r /tmp/build.txt
COPY requirements/base.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY . /opt/eve
RUN pip3 install --no-deps /opt/eve

COPY eve/etc/master.cfg /root/eve
COPY buildbot.tac /root/eve
COPY docker_cmd.py /root/eve

CMD /root/eve/docker_cmd.py
