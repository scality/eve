from __future__ import print_function

import os

from tests.util.crossbar.crossbar_conf_factory import CrossbarConfFactory
from tests.util.daemon import Daemon


class Crossbar(Daemon):
    start_success_msg = \
        "Router 'worker-001': transport 'transport-001' started"
    _log = 'node.log'
    _start_cmd = ['crossbar', 'start', '--logtofile', '--cbdir', '.']
    _env = os.environ
    _start_wait = 20

    def __init__(self):
        """
        Crossbar Daemon
        """
        self.port = self.get_free_port()
        super(Crossbar, self).__init__(name='crossbar_{}'.format(self.port))

    def pre_start_hook(self):
        """Generates the conf file before the crossbar daemon is spawned
        """
        conf = CrossbarConfFactory(port=self.port)
        conf.dump(os.path.join(self._base_path, 'config.json'))
