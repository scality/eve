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

MYSQL_ROOT_PASSWORD = '4m4zingroot'
MYSQL_DATABASE = 'buildbot_db'
MYSQL_USER = 'eve'
MYSQL_PASSWORD = '4m4zing'


class DockerizedMySQL(Daemon):
    _post_start_delay = 1
    _start_wait = 120
    start_success_msg = 'MySQL init process done. Ready for start up.'
    _stop_cmd = 'docker rm -f {name}'

    def __init__(self, external_ip='localhost'):
        """Represent a dockerized MySQL daemon.

        Args:
            external_ip (str): The IP address that will allow external access.

        """
        self.port = self.get_free_port()
        super(DockerizedMySQL,
              self).__init__(name='mysql_{}'.format(self.port))
        self.url = 'mysql://{}:{}@{}:{}/{}?max_idle=300'.format(
            MYSQL_USER, MYSQL_PASSWORD, external_ip, self.port, MYSQL_DATABASE)
        self._start_cmd = None

    def pre_start_hook(self):
        """Pull a mysql docker image and prepare the command to run it."""
        cmd('docker pull mysql/mysql-server:5.7')
        self._start_cmd = [
            'docker', 'run', '--name', self._name,
            '-p', '{}:3306'.format(self.port),
            '-e', 'MYSQL_ROOT_PASSWORD={}'.format(MYSQL_ROOT_PASSWORD),
            '-e', 'MYSQL_DATABASE={}'.format(MYSQL_DATABASE),
            '-e', 'MYSQL_USER={}'.format(MYSQL_USER),
            '-e', 'MYSQL_PASSWORD={}'.format(MYSQL_PASSWORD),
            'mysql/mysql-server:5.7'
        ]  # yapf: disable

    def _log(self):
        """Return the logs of the MySQL docker container."""
        return cmd('docker logs {}'.format(self._name))
