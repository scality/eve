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

from tests.util.cmd import cmd
from tests.util.daemon import Daemon


class DockerizedRegistry(Daemon):
    _post_start_delay = 1
    _stop_cmd = 'docker rm -f {name}'

    def __init__(self, external_ip='localhost'):
        self.external_ip = external_ip
        self.port = self.get_free_port()
        super(DockerizedRegistry,
              self).__init__(name='registry_{}'.format(self.port))
        self._start_cmd = None

    def pre_start_hook(self):
        cmd('docker pull registry:2')
        self._start_cmd = [
            'docker', 'run', '--name', self._name, '-p',
            '{}:5000'.format(self.port), 'registry:2'
        ]

    def _log(self):
        """Return the logs of the Crossbar docker container."""
        return cmd('docker logs {}'.format(self._name))
