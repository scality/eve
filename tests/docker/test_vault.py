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

import unittest

from tests.docker.vault import DockerizedVault


class TestVault(unittest.TestCase):
    def test_start_stop(self):
        """Test that the vault docker works properly

         Steps:
           - start the vault container
           - store a secret
           - read the secret and check its value
           - stop the container
        """
        vault = DockerizedVault(external_ip='localhost')
        vault.start()
        vault.write_secret('foo', {'value': 'bar'})
        assert vault.read_secret('foo') == {'value': 'bar'}
        vault.stop()
