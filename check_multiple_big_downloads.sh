#!/bin/bash

mkdir download
cd download

for i in `seq 0 9`
do
    wget -q -O data.$i $1 &
done
wait

for i in `seq 0 9`
do
    cat ../big/data.sha1 | sed -e "s/data/data.$i/" >> data.sha1
done

ls -l ../big/data
cat ../big/data.sha1
ls -l data*
cat data.sha1
sha1sum -c data.sha1
