FROM ubuntu:trusty

EXPOSE 9418

RUN apt-get update -qq
RUN apt-get install -qqy git

RUN mkdir /srv/git

RUN git init --bare /srv/git/repo.git

CMD git daemon --export-all --base-path=/srv/git --listen=0.0.0.0 --port=9418 --enable=receive-pack
