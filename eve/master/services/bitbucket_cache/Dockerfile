FROM ubuntu:trusty

# Set to 1 to activate mock mode (Does not access the real bitbucket.org)
ARG MOCK=0

RUN apt-get update

RUN apt-get install -qy nginx git openssh-server
RUN mkdir -p /etc/nginx/ssl/
COPY scality_bitbucket_config.txt /tmp/scality_bitbucket_config.txt
RUN openssl req -batch -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt -config /tmp/scality_bitbucket_config.txt \
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

RUN /bin/echo -e 'bitbucket.org,104.192.143.1 ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAubiN81eDcafrgMeLzaFPsw2kNvEcqTKl/VqLat/MaB33pZy0 y3rJZtnqwR2qOOvbwKZYKiEO1O6VqNEBxKvJJelCq0dTXWT5pbO2gDXC6h6QDXCaHo6pOHGPUy+YBaGQRGuSusMEASYiWunYN0vCAI8QaXnWMXNMdFP3jHAJH0eDsoiGnLPBlBp4TNm6rYI74nMzgz3B9IikW4WVK+dc8KZJZWYjAuORU3jc1c/NPskD2ASinf8v3xnfXeukU0sJ5N6m5E8VLjObPEO+mN2t/FZTMZLiFqPWc/ALSqnMnnhwrNi2rbfg/rd/IpL8Le3pSBne8+seeFVBoGqzHM9yXw==\n\
bitbucket.org,104.192.143.2 ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAubiN81eDcafrgMeLzaFPsw2kNvEcqTKl/VqLat/MaB33pZy0y3rJZtnqwR2qOOvbwKZYKiEO1O6VqNEBxKvJJelCq0dTXWT5pbO2gDXC6h6QDXCaHo6pOHGPUy+YBaGQRGuSusMEASYiWunYN0vCAI8QaXnWMXNMdFP3jHAJH0eDsoiGnLPBlBp4TNm6rYI74nMzgz3B9IikW4WVK+dc8KZJZWYjAuORU3jc1c/NPskD2ASinf8v3xnfXeukU0sJ5N6m5E8VLjObPEO+mN2t/FZTMZLiFqPWc/ALSqnMnnhwrNi2rbfg/rd/IpL8Le3pSBne8+seeFVBoGqzHM9yXw==\
' >> /home/git/.ssh/known_hosts

# configure ssh server and start it
RUN sed -ri 's/nullok_secure/nullok/' /etc/pam.d/common-auth
RUN sed -ri '/PermitEmptyPasswords/d' /etc/ssh/sshd_config

RUN echo 'AllowUsers git' >> /etc/ssh/sshd_config
RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config
RUN echo 'PermitEmptyPasswords yes' >> /etc/ssh/sshd_config
RUN echo 'ForceCommand /usr/bin/flock -w 120 /var/lock/bitbucket_cache.lock -c /home/git/gitmirror_access_via_ssh.sh' >> /etc/ssh/sshd_config


RUN chown -R git:git /home/git
USER git
RUN mkdir /home/git/scality/
WORKDIR /home/git/scality
RUN git init --bare mock.git
VOLUME /home/git/scality/

USER root
CMD /root/gitmirror_init.sh && tail -f /dev/null
