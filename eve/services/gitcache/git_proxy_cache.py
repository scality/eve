#!/usr/bin/python

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

import os

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
    os.execlp('git', 'git', 'remote', 'update', '--prune')
else:
    # This is the first time this repo is requested.
    # creating the cache parent folder...
    try:
        os.makedirs(os.path.join(repocachedir, os.pardir))
    except OSError:
        pass

    remote_url = '{}://{}/{}/{}'.format(scheme, githost, account, reponame)

    os.execlp('git',
              'git',
              'clone',
              '--quiet',
              '--mirror',
              remote_url,
              repocachedir)
