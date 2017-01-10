#!/bin/bash
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
