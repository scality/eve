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

import socket
from unittest import TestCase

from tests.util.cmd import cmd
from tests.util.daemon.daemon import Daemon


class SleepyDaemon(Daemon):
    """A fake daemon for testing purposes. It just sleeps for 1 hour."""
    _start_cmd = ['sleep', '3600']


class TestPorts(TestCase):
    @staticmethod
    def is_free(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', port))
        sock.close()

    def test_single_port_request_is_free(self):
        self.is_free(Daemon.get_free_port())

    def test_multi_ports_request(self):
        ports = Daemon.get_free_port(3)
        for port in ports:
            self.is_free(port)
        self.assertNotEqual(ports[0], ports[1])
        self.assertNotEqual(ports[0], ports[2])
        self.assertNotEqual(ports[1], ports[2])


class TestDaemon(TestCase):
    def test_start_stop_sleepy_daemon(self):
        """Test start and stop a fake daemon.

        Steps:
            - Start a fake daemon and.
            - Check that it exists in `ps aux`.
            - Stop it.
            - Check that it disapeared from `ps aux`.

        """
        fake_daemon = SleepyDaemon('sleep1H')
        fake_daemon.start()
        self.assertIn('sleep 3600', cmd('ps aux'), 'Daemon did not start')
        fake_daemon.stop()
        self.assertNotIn('sleep 3600', cmd('ps aux'), 'Daemon did not stop')
