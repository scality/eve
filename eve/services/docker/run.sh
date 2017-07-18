#!bin/bash

docker login -u oauth2accesstoken -p "$(gcloud auth application-default print-access-token)" https://gcr.io

redis-server > /var/log/redis.log &
for i in $(seq 3); do
    celery -A app.celery worker --concurrency=10 -n worker$i@%h > /var/log/celery$i.log &
done
flask run --host=0.0.0.0
