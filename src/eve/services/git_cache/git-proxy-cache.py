#!/usr/bin/python

import os
import subprocess

project_root = os.environ['GIT_PROJECT_ROOT']
reporelpath = os.environ['PATH_INFO']
# e.g. reporelpath = /github.com/organization/myrepo.git/info/refs

_, githost, account, reponame, _ = reporelpath.split('/', 4)
repocachedir = os.path.join(project_root, githost, account, reponame)

# if a cached repository already exists, we just refresh it.
if os.path.exists(repocachedir):
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

    if githost == 'mock':
        # for testing purposes, we can use mock as an organization. In this
        # case, the repo is dynamically created locally with write access.
        subprocess.check_output(['git',
                                 'init',
                                 '--bare',
                                 '--quiet',
                                 repocachedir])
        os.chdir(repocachedir)
        subprocess.check_output(['git',
                                 'config',
                                 'http.receivepack',
                                 'true'])

    else:
        # We need to clone a remote repo to create the cache.
        remote_url = 'https://{}/{}/{}'.format(githost, account, reponame)
        subprocess.check_output(['git',
                                 'clone',
                                 '--quiet',
                                 '--mirror',
                                 remote_url,
                                 repocachedir])
