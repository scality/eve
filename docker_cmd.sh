#!/usr/bin/env bash

#set -e
buildbot create-master --db=$DB_URL . || exit 1

# wait for database to wake up
n=0
until [ $n -ge 60 ]
do
    buildbot upgrade-master . && break  # substitute your command here
    n=$[$n+1]
    echo "Buildbot upgrade failed ? Is the database available ?"
    sleep 1
done

buildbot upgrade-master . || exit 1
echo "Starting daemon..."
buildbot start .  || exit 1
tail -fn 1000 twistd.log
