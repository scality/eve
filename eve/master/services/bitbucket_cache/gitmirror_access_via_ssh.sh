#!/bin/bash

# ensure the command is allowed
ACCEPTED_PATTERNS="git-upload-pack '[a-zA-Z_-]+/[a-zA-Z_-]+\.git'"
if ! $(echo "$SSH_ORIGINAL_COMMAND" | grep -qE "$ACCEPTED_PATTERNS")
then
    echo "only git-upload-pack commands are allowed. Received '$SSH_ORIGINAL_COMMAND'"
    exit 1
fi

# clone the repo if not done yet

repo=$(echo "$SSH_ORIGINAL_COMMAND" | sed -re "s/^.*'[a-zA-Z_-]+\/([a-zA-Z_-]+)\.git'/\1/")
repo_dest=/home/git/scality/$repo.git
if [ ! -d "$repo_dest" ]
then
    git clone --mirror git@bitbucket.org:scality/$repo $repo_dest
fi

cd $repo_dest;
if [ ! "$repo" = 'mock' ];
then
    git remote update;
fi


# execute git-upload-pack
sh -c "$SSH_ORIGINAL_COMMAND"
