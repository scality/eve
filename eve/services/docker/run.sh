#!bin/bash

# refuse to run if kubectl client version does not match server
client=$(kubectl version --short | \
         sed -n 's/Client Version: v*\([0-9]\.[0-9]\.[0-9]\).*/\1/p')
server=$(kubectl version --short | \
         sed -n 's/Server Version: v*\([0-9]\.[0-9]\.[0-9]\).*/\1/p')
echo "kubectl client version: $client"
echo "kubectl server version: $server"
test -z "$client" && \
    echo "could not parse kubectl version" && \
    exit 1
test ! "$client" = "$server" && \
    echo "warning: kubectl version mismatch"

while true; do
    RES=$(docker login \
            -u oauth2accesstoken \
            -p "$(gcloud auth application-default print-access-token)" \
            https://gcr.io 2>&1)
    echo "$(date) ${RES}" >> /var/log/docker_login.log
    sleep 2400
done &

redis-server > /var/log/redis.log &

for i in $(seq 3); do
    celery -A app.celery worker \
           --concurrency=10 \
           -n worker$i@%h > /var/log/celery$i.log &
done

flask run --host=0.0.0.0
