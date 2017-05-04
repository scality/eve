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

from os import pardir
from os.path import join

from tests.util.cmd import cmd
from tests.util.crossbar import Crossbar


class DockerizedCrossbar(Crossbar):
    _post_start_delay = 1
    _stop_cmd = 'docker rm -f {name}'

    def pre_start_hook(self):
        """
        Creates a crossbar configuration, pulls the crossbar docker image and
         prepares the command to run it
        """

        conf = join(__file__, pardir, pardir, 'util', 'crossbar',
                    'crossbar.json')
        cmd('docker pull crossbario/crossbar')
        self._start_cmd = [
            'docker', 'run',
            '--name', self._name,
            '-p', '{}:10990'.format(self.port),
            '-v', '{}:/node/.crossbar/config.json'.format(conf),
            'crossbario/crossbar'
        ]  # yapf: disable

    def _log(self):
        """
        Returns: the logs of the Crossbar docker container
        """
        return cmd('docker logs {}'.format(self._name))
