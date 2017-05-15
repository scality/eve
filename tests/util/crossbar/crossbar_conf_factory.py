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

import json
import os


class CrossbarConfFactory(object):
    master_count = 0

    def __init__(self, port=None):
        """Generate Crossbar configuration.

        Args:
            port (int): The port number to use (optional).

        """
        json_conf_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'crossbar.json')

        with open(json_conf_path) as fhandle:
            self._conf = json.load(fhandle)
        if port is not None:
            self._conf['workers'][0]['transports'][0]['endpoint']['port'] = \
                port

    def dump(self, filename):
        """Dump the conf to a file.

        Args:
            filename (str): The file path to dump the conf to.

        """
        with open(filename, 'w') as fhandle:
            json.dump(self._conf, fhandle)
