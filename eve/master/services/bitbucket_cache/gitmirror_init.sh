#!/bin/bash

# give git ssh keys
cp /root/.ssh/id_rsa* /home/git/.ssh/
chown -R git:git /home/git/.ssh
chmod 600 /home/git/.ssh/id_rsa

service nginx start
service ssh start
