#!/bin/bash

# ensure the command is allowed
ACCEPTED_PATTERNS="git-upload-pack '[a-zA-Z_-]+/[a-zA-Z_-]+\.git'"
if ! $(echo "$SSH_ORIGINAL_COMMAND" | grep -qE "$ACCEPTED_PATTERNS")
then
    echo "only git-upload-pack commands are allowed. Received '$SSH_ORIGINAL_COMMAND'"
    exit 1
fi

# clone the repo if not done yet
(
    repo=$(echo "$SSH_ORIGINAL_COMMAND" | sed -re "s/^.*'scality\/([a-zA-Z_-]+)\.git'/\1/")
    repo_dest=/home/git/scality/$repo.git
    if [ ! -d "$repo_dest" ]
    then
        if [ ! "$repo" = 'mock' ];
        then
            cd $repo_dest;
            git remote update || exit 1;
        fi
    else
        mkdir -p /home/git/scality
        git clone --mirror git@bitbucket.org:scality/$repo $repo_dest || exit 1
    fi
) > /dev/null || exit 1


# execute git-upload-pack
sh -c "$SSH_ORIGINAL_COMMAND"
