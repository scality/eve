FROM debian:stable
RUN apt-get update && apt-get install -y \
   python-dev \
   python-pip \
   git

RUN pip install buildbot-worker==0.9.0b9
RUN groupadd -r buildbot && useradd -r -g buildbot buildbot
RUN mkdir /worker && chown buildbot:buildbot /worker


# Copy over private key, and set permissions
RUN mkdir /root/.ssh/
COPY docker_worker/git_certs/id_rsa /root/.ssh/id_rsa
COPY docker_worker/git_certs/id_rsa.pub /root/.ssh/id_rsa.pub
RUN ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts
RUN ls
RUN git clone git@bitbucket.org:scality/test_buildbot.git

# USER buildbot
# RUN mkdir -p /home/buildbot/.ssh
WORKDIR /worker
ENTRYPOINT ["/usr/local/bin/buildbot-worker"]
CMD buildbot-worker create-worker . $BUILDMASTER $WORKERNAME $WORKERPASS && start --nodaemon