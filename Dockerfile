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
        python-dev \
        python-pip \
        python-psycopg2 \
        telnet \
        vim.tiny && \
    rm -rf /var/lib/apt/lists/*


ARG DOCKER_VERSION=18.06.1~ce~3-0~ubuntu
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - \
 && echo "deb [arch=amd64] https://download.docker.com/linux/ubuntu xenial stable" \
    | tee -a /etc/apt/sources.list.d/docker-ce.list \
 && apt-get update \
 && apt-get install -y -q docker-ce=${DOCKER_VERSION}


# Install git lfs
RUN echo "deb https://packagecloud.io/github/git-lfs/ubuntu/ xenial main" > /etc/apt/sources.list.d/github_git-lfs.list && \
    curl -sSL https://packagecloud.io/github/git-lfs/gpgkey | apt-key add - && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install -q git-lfs && \
    git lfs install --system --skip-smudge --skip-repo

RUN pip install --upgrade pip==9.0.2

WORKDIR /root/eve

# Freezing requirements
COPY requirements/base.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY . /opt/eve
RUN pip install --no-deps /opt/eve

COPY eve/etc/master.cfg /root/eve
COPY buildbot.tac /root/eve
COPY docker_cmd.py /root/eve

CMD /root/eve/docker_cmd.py
