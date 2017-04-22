#!/usr/bin/python

import os
import subprocess

project_root = os.environ['GIT_PROJECT_ROOT']
reporelpath = os.environ['PATH_INFO']
# e.g. reporelpath = /github.com/organization/myrepo.git/info/refs

_, scheme, githost, account, reponame, _ = reporelpath.split('/', 5)
repocachedir = os.path.join(project_root, scheme, githost, account, reponame)

# if a cached repository already exists, we just refresh it.
if os.path.exists(repocachedir):
    try:
        os.makedirs(repocachedir)
    except OSError:
        pass
    os.chdir(repocachedir)
    subprocess.check_output(['git',
                             'remote',
                             'update',
                             '--prune'])
else:
    # This is the first time this repo is requested.
    # creating the cache parent folder...
    try:
        os.makedirs(os.path.join(repocachedir, os.pardir))
    except OSError:
        pass

    remote_url = '{}://{}/{}/{}'.format(scheme, githost, account, reponame)

    subprocess.check_output(['git',
                             'clone',
                             '--quiet',
                             '--mirror',
                             remote_url,
                             repocachedir])
