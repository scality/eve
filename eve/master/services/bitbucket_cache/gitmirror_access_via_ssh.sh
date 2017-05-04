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

set -e

LOG_FILE=~/bitbucket_cache.log
# ensure the command is allowed
ACCEPTED_PATTERNS="git-[/a-zA-Z]+-pack '[/a-zA-Z_-]+/[a-zA-Z_-]+\.git'"
if ! $(echo "$SSH_ORIGINAL_COMMAND" | grep -qE "$ACCEPTED_PATTERNS")
then
    echo "only git-*-pack commands are allowed. Received '$SSH_ORIGINAL_COMMAND'" | tee -a ${LOG_FILE}
    exit 1
fi

# clone the repo if not done yet
(
    repo=$(echo "$SSH_ORIGINAL_COMMAND" | sed -re "s/^.*'[/a-zA-Z_-]+\/([a-zA-Z_-]+)\.git'/\1/")
    repo_dest=/home/git/scality/$repo.git
    if [ -d "$repo_dest" ]
    then
        cd $repo_dest;
        git remote update || exit 1;
    else
        mkdir -p /home/git/scality
        git clone --mirror git@bitbucket.org:scality/$repo.git $repo_dest || exit 1
    fi
) >> ${LOG_FILE} 2>&1 || exit 1


# execute git-upload-pack
sh -c "$SSH_ORIGINAL_COMMAND"
