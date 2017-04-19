from os import pardir
from os.path import join

from tests.util.cmd import cmd
from tests.util.crossbar import Crossbar


class DockerizedCrossbar(Crossbar):
    _post_start_delay = 1
    _stop_cmd = 'docker rm -f {name}'

    def pre_start_hook(self):
        """Spawns a dockerized crossbar.
        """

        conf = join(__file__, pardir, pardir, 'util', 'crossbar',
                    'crossbar.json')
        self._start_cmd = [
            'docker', 'run',
            '--name', self._name,
            '-p', '{}:10990'.format(self.port),
            '-v', '{}:/node/.crossbar/config.json'.format(conf),
            'crossbario/crossbar'
        ]  # yapf: disable

    def _log(self):
        return cmd('docker logs {}'.format(self._name))
