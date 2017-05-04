#!/bin/bash

# Copyright 2017 Scality
#
# This file is part of Eve.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.

# give git ssh keys
cp /root/.ssh/id_rsa_eve /home/git/.ssh/id_rsa
cp /root/.ssh/id_rsa_eve.pub /home/git/.ssh/id_rsa.pub
chown -R git:git /home/git/.ssh
chmod 600 /home/git/.ssh/id_rsa

service nginx start
service ssh start
