FROM ubuntu:xenial

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install -q \
        wget && \
    rm -rf /var/lib/apt/lists/*

RUN wget https://storage.googleapis.com/kubernetes-release/release/v1.9.0/bin/linux/amd64/kubectl \
 && chmod +x kubectl

COPY entrypoint /entrypoint
ENTRYPOINT ["/entrypoint"]
