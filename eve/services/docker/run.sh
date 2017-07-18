#!bin/bash

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
