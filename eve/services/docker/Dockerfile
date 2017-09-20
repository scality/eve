FROM ubuntu:xenial

ENV PATH="/opt/google-cloud-sdk/bin:${PATH}"
ENV GOOGLE_APPLICATION_CREDENTIALS=/creds/creds.json
ENV CLOUDSDK_PYTHON_SITEPACKAGES 1
ENV FLASK_APP /app.py

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install -q \
        python \
        python-pip \
        redis-server \
        unzip \
        wget && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade \
        celery \
        flask \
        jinja2 \
        redis

# Install docker.
RUN wget -qO- https://get.docker.com/ | sh
RUN ln -s /usr/bin/docker /usr/local/bin/docker

# Install google cloud SDK.
RUN cd /opt \
    && wget https://dl.google.com/dl/cloudsdk/channels/rapid/google-cloud-sdk.zip \
    && unzip google-cloud-sdk.zip \
    && rm google-cloud-sdk.zip \
    && /opt/google-cloud-sdk/install.sh --additional-components kubectl \
    && gcloud config set --installation component_manager/disable_update_check true \
    && sed -i -- 's/"disable_updater": false/"disable_updater": true/g' /opt/google-cloud-sdk/lib/googlecloudsdk/core/config.json

RUN mkdir /creds
COPY creds.json /creds/
COPY run.sh /
COPY app.py /
COPY command.py /
COPY templates /templates
COPY commands /commands

VOLUME "/var/lib/docker" "/var/log" "/resource"

CMD ["/run.sh"]
