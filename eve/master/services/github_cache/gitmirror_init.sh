#!/bin/bash

# give git ssh keys
cp /root/.ssh/id_rsa_github /home/git/.ssh/id_rsa
cp /root/.ssh/id_rsa_github.pub /home/git/.ssh/id_rsa.pub
chown -R git:git /home/git/.ssh
chmod 600 /home/git/.ssh/id_rsa

service ssh start
