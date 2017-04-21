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
