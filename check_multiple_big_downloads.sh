#!/bin/bash

full_url=$1
host=$(echo $full_url | cut -d/ -f3 | cut -d: -f1)
port=$(echo $full_url | cut -d/ -f3 | cut -d: -f2)
uri=/$(echo $full_url | cut -d/ -f4-)
[ "$host" != "$port" ] || port="80"

mkdir download
cd download

# try to mess the uwsgi cache with concurrent interrupted GET operations while downloading the data
wget -q -O data.before $full_url &
for i in `seq 0 9`
do
    bytes=$(( 1000000000 + $i * 100000000))
    (/bin/echo -e "GET $uri HTTP/1.1\nHost: $host\n\n" | nc $host $port | head -c $bytes > /dev/null)&
done
wget -q -O data.after $full_url &
wait

# launch concurrent complete downloads
for i in `seq 0 9`
do
    wget -q -O data.$i $full_url &
done
wait

# check complete downloads
cat ../big/data.sha1 | sed -e "s/data/data.before/" >> data.sha1
cat ../big/data.sha1 | sed -e "s/data/data.after/" >> data.sha1
for i in `seq 0 9`
do
    cat ../big/data.sha1 | sed -e "s/data/data.$i/" >> data.sha1
done
sha1sum -c data.sha1
