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

import platform

from tests.docker.buildbot_master import DockerizedBuildbotMaster
from tests.docker.crossbar import DockerizedCrossbar
from tests.docker.mysql import DockerizedMySQL
from tests.util.cluster import Cluster
from tests.util.cmd import cmd
from tests.util.githost_mock.githost_mock import GitHostMock


class DockerizedCluster(Cluster):
    _ext_ip = None
    githost_class = GitHostMock
    db_class = DockerizedMySQL
    crossbar_class = DockerizedCrossbar
    buildbot_master_class = DockerizedBuildbotMaster

    @property
    def external_ip(self):
        """Return the external IP address of the cluster.

        On Linux, it returns '172.17.0.1'
        On Mac OS, it tries to find the address that connects your computer to
        the Internet.

        """
        if self._ext_ip:
            return self._ext_ip
        if platform.system() == 'Darwin':
            self._ext_ip = cmd(
                # pylint: disable=anomalous-backslash-in-string
                "ifconfig | grep -E '([0-9]{1,3}\.){3}[0-9]{1,3}'"
                " | grep -v 127.0.0.1"
                " | awk '{ print $2 }' | cut -f2 -d:"
                " | head -n1").strip()
            assert self._ext_ip, 'Not connected to the internet ?'
            return self._ext_ip
        else:
            self._ext_ip = '172.17.0.1'  # Should work on Linux systems
        return self._ext_ip
