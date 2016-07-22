FROM ubuntu

EXPOSE :80
EXPOSE :443
EXPOSE :9989

# Install buildbot and its dependencies
RUN apt-get update -y
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python-pip \
    wget \
    python-dev \
    libssl-dev \
    libffi-dev \
    ca-certificates \
    nginx \
    git

RUN wget --no-verbose --tries=3 --timeout=30 https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py pip==8.1.2
COPY requirements.txt requirements.txt
RUN /usr/local/bin/pip install -r requirements.txt

# Configure nginx as a reverse proxy
COPY etc/nginx-eve.conf /etc/nginx/sites-available/eve.conf
COPY etc/htpasswd /etc/nginx/htpasswd
RUN rm /etc/nginx/sites-enabled/default
RUN ln -s /etc/nginx/sites-available/eve.conf /etc/nginx/sites-enabled/eve.conf




#


# Create buildbot folder
RUN buildbot create-master master

# Copy buildbot configuration
COPY master.cfg.py master/master.cfg

COPY certs master/certs
ENV DOCKER_CERT_PATH certs/docker_workers

# Copy over private key and set permissions
RUN mkdir /root/.ssh/
RUN mv master/certs/git/id_rsa /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa
RUN ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts 2> /dev/null

CMD \
       buildbot start master \
    && git clone git@bitbucket.org:scality/wall-e.git \
    && /etc/init.d/nginx start ; tail -f master/twistd.log
