FROM ubuntu:xenial


ENV \
  GIT_GROUP="${GIT_GROUP:-www-data}"

RUN \
  apt-get update && \
  apt-get install -y fcgiwrap git nginx python && \
  echo "\ndaemon off;" >> /etc/nginx/nginx.conf && \
  mkdir -p /data/nginx && \
  rm -rf /var/lib/apt/lists/* && \
  chown -R www-data:www-data /var/lib/nginx && \
  mkdir /git && \
  touch /git/.git-credentials  # empty by default, override in a volume if required

VOLUME ["/var/lib/git", "/data/nginx", "/var/log"]

COPY git_proxy_cache.py /usr/lib/git-core/git_proxy_cache.py
COPY git-proxy-cache-and-http-backend /usr/lib/git-core/git-proxy-cache-and-http-backend
COPY git-nginx-conf /etc/nginx/sites-enabled/default

RUN \
  chmod 777 /usr/lib/git-core/git-proxy-cache-and-http-backend && \
  git config --system credential.helper 'store --file=/var/lib/git/.git-credentials'

CMD \
  cp /git/.git-credentials /var/lib/git && \
  chown -R www-data:www-data /var/lib/git && \
  echo "FCGI_GROUP=${GIT_GROUP}" > /etc/default/fcgiwrap && \
  service fcgiwrap start && \
  service nginx start
