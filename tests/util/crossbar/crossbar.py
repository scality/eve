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

from __future__ import print_function

import os

from tests.util.crossbar.crossbar_conf_factory import CrossbarConfFactory
from tests.util.daemon import Daemon


class Crossbar(Daemon):
    start_success_msg = \
        """Ok, worker "Router worker001" configured and ready!"""
    _log = 'node.log'
    _start_cmd = ['crossbar', 'start', '--logtofile', '--cbdir', '.']
    _env = os.environ
    _start_wait = 20

    def __init__(self):
        """Crossbar Daemon."""
        self.port = self.get_free_port()
        super(Crossbar, self).__init__(name='crossbar_{}'.format(self.port))

    def pre_start_hook(self):
        """Generate the conf file before the crossbar daemon is spawned."""
        conf = CrossbarConfFactory(port=self.port)
        conf.dump(os.path.join(self._base_path, 'config.json'))
