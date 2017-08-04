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

from tests.util.buildbot_master import BuildbotMaster
from tests.util.cmd import cmd


class DockerizedBuildbotMaster(BuildbotMaster):
    _post_start_delay = 1
    _stop_cmd = 'docker rm -f {name}'

    def __init__(self, *args, **kwargs):
        """Dockerized buildbot master daemon.

        Args:
            *args: Same as the BuildbotMaster class.
            **kwargs: Same as the BuildbotMaster class.

        """
        super(DockerizedBuildbotMaster, self).__init__(*args, **kwargs)
        self._env_file = os.path.join(self._base_path, 'docker.env')
        port = self.conf.get('PB_PORT')
        self._start_cmd = [
            'docker', 'run',
            '--name', self._name,
            '-p', '{0}:{0}'.format(self.conf.get('HTTP_PORT')),
            '-p', '{0}:{0}'.format(port),
            '-e', 'EXTERNAL_PB_PORT={}'.format(port),
            '-v', '/var/run/docker.sock:/var/run/docker.sock',
            '--env-file', self._env_file,
            'eve_master'
        ]

    def pre_start_hook(self):
        """Build an eve docker image and prepare the environment to run it."""
        cmd('docker build -t eve_master  .')
        self._env = self.environ
        self.dump(self._env_file)

    def _log(self):
        """Return the logs of the buildbot docker container."""
        return cmd('docker logs {}'.format(self._name))
