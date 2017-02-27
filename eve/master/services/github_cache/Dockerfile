FROM ubuntu:trusty

# Set to 1 to activate mock mode (Does not access the real github.com)
ARG MOCK=0

RUN apt-get update

RUN apt-get install -qy nginx git openssh-server
RUN mkdir -p /etc/nginx/ssl/
COPY scality_github_config.txt /tmp/scality_github_config.txt
RUN openssl req -batch -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt -config /tmp/scality_github_config.txt
 && chmod 400 /etc/nginx/ssl/nginx.key
RUN mkdir -p /data/nginx
COPY rproxy.conf /etc/nginx/sites-available/rproxy.conf
RUN chmod 400 /etc/nginx/sites-available/rproxy.conf
RUN rm -f /etc/nginx/sites-enabled/default \
 && ln -s /etc/nginx/sites-available/rproxy.conf /etc/nginx/sites-enabled/rproxy.conf

COPY gitmirror_init.sh /root/
RUN chmod +x /root/*.sh

# create user git
RUN useradd -ms /bin/bash git
RUN passwd -d git

COPY gitmirror_access_via_ssh.sh /home/git/
RUN chmod +x /home/git/gitmirror_access_via_ssh.sh

RUN mkdir -p /home/git/.ssh

RUN /bin/echo -e 'github.com ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ==\
' >> /home/git/.ssh/known_hosts

# configure ssh server and start it
RUN sed -ri 's/nullok_secure/nullok/' /etc/pam.d/common-auth
RUN sed -ri '/PermitEmptyPasswords/d' /etc/ssh/sshd_config

RUN echo 'AllowUsers git' >> /etc/ssh/sshd_config
RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config
RUN echo 'PermitEmptyPasswords yes' >> /etc/ssh/sshd_config
RUN echo 'ForceCommand /usr/bin/flock -w 120 /var/lock/github_cache.lock -c /home/git/gitmirror_access_via_ssh.sh' >> /etc/ssh/sshd_config


RUN chown -R git:git /home/git
USER git
RUN mkdir /home/git/scality/
WORKDIR /home/git/scality
RUN git init --bare mock.git

USER root
CMD /root/gitmirror_init.sh && tail -f /dev/null
