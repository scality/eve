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

import requests
from tests.util.cmd import cmd
from tests.util.daemon import Daemon

ROOT_TOKEN = 'myroot'


class DockerizedVault(Daemon):
    _post_start_delay = 1
    _start_wait = 120
    start_success_msg = '==> Vault server started!'
    _stop_cmd = 'docker rm -f {name}'

    def __init__(self, external_ip='localhost'):
        """Represent a dockerized Hashicoprp Vault daemon.

        Args:
            external_ip (str): The IP address that will allow external access
        """
        self.port = self.get_free_port()
        super(DockerizedVault,
              self).__init__(name='vault_{}'.format(self.port))
        self.url = 'http://{}:{}'.format(external_ip, self.port)
        self._start_cmd = None
        self.__token = None

    def pre_start_hook(self):
        """Pull a vault docker image and prepare the command to run it."""
        cmd('docker pull library/vault:0.7.0')
        self._start_cmd = [
            'docker', 'run', '--name', self._name,
            '--cap-add=IPC_LOCK',
            '-e', 'VAULT_DEV_ROOT_TOKEN_ID={}'.format(ROOT_TOKEN),
            '-e', 'VAULT_ADDR=http://localhost:8200',
            '-p', '{}:8200'.format(self.port),
            'vault:0.7.0'
        ]

    @property
    def token(self):
        """Return the VAULT authentication token."""

        if not self.__token:
            res = requests.post(
                self.url + '/v1/auth/token/create',
                headers={'X-Vault-Token': ROOT_TOKEN})
            res.raise_for_status()
            self.__token = res.json()['auth']['client_token']
        return self.__token

    def write_secret(self, name, data):
        """Write a secret."""

        assert isinstance(data, dict)
        res = requests.post(
            self.url + '/v1/secret/{}'.format(name),
            headers={'X-Vault-Token': self.token},
            json=data)
        res.raise_for_status()

    def read_secret(self, name):
        """Read a secret."""

        res = requests.get(
            self.url + '/v1/secret/{}'.format(name),
            headers={'X-Vault-Token': self.token})
        res.raise_for_status()
        return res.json()['data']

    def _log(self):
        """Return the logs of the Vault docker container."""
        return cmd('docker logs {}'.format(self._name))
