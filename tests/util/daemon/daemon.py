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

import atexit
import socket
import tempfile
import time
from os import environ
from os.path import join
from subprocess import Popen

from tests.util.cmd import cmd


class Daemon(object):
    _log = None
    _status = None
    _start_cmd = None
    _start_wait = None
    _stop_cmd = None
    _env = environ
    _post_start_delay = 0
    start_success_msg = None

    def __init__(self, name):
        """Specify a daemon that can be interacted with.

        Args:
            name (str): The name of the daemons (displayed in logs).

        """
        self._name = name
        self._base_path = tempfile.mkdtemp(
            prefix=str(time.time()), suffix='_eve_{}'.format(self._name))
        self._process = None

    def pre_start_hook(self):
        """Prepare for daemon startup."""

    def start(self):
        """Start the daemon and eventually wait for it.

        Returns:
            self

        """
        self.pre_start_hook()
        print(' '.join(self._start_cmd))
        self._process = Popen(
            self._start_cmd, env=self._env, cwd=self._base_path)
        self._status = 'starting'
        atexit.register(self.kill)
        time.sleep(self._post_start_delay)

        if self._start_wait is not None:
            self.wait_for_it(self._start_wait)
        return self

    def kill(self):
        """SIGKILL the daemon violently.

        This should be avoided. Try to kill the daemons cleanly in
        teardown methods with stop().

        """
        if self._process.returncode is not None:
            return  # The child exited properly
        print('WARNING: {} PID: {} has not been shutdown properly in tests. '
              'Forcing shutdown...'.format(self._name, self._process.pid))
        self._process.kill()

    def stop(self):
        """Send a SIGTERM to the daemon and wait until it finishes."""
        print(
            'terminating {} PID: {}...'.format(self._name, self._process.pid))
        if self._stop_cmd is not None:
            cmd(self._stop_cmd.format(name=self._name), cwd=self._base_path)
            # self.wait_for_it()
        else:
            self._process.terminate()
        for _ in range(30):
            if self._process.poll() is not None:
                time.sleep(1)  # allow logs to flush to disk
                return
            print('process still here, retry in 1s')
            time.sleep(1)
        raise Exception(
            '{} never stopped {}'.format(self._name, self._process.pid))

    @property
    def loglines(self):
        """Return a list of the daemon's log lines."""
        if self._log is None:
            return []
        if callable(self._log):
            # pylint: disable=not-callable
            return self._log().split('\n')

        return open(join(self._base_path, self._log)).readlines()

    def print_loglines(self):
        """Print the log of the daemon."""
        for logline in self.loglines:
            print('{}: {}'.format(self._name, logline), end='')

    def wait_for_it(self, delay=10):
        """Wait for the daemon to start / stop.

        Args:
            delay (int): Number of seconds after which an exception is raised.

        """
        for _ in xrange(delay):
            if self._status == 'stopping':
                if self._process.returncode is None:
                    return
            else:
                # self._status == starting
                try:
                    self.sanity_check()
                    for logline in self.loglines:
                        if self.start_success_msg in logline:
                            print('*' * 30, '{} is running'.format(self._name))
                            return
                except IOError:
                    pass
            time.sleep(1)
        self.print_loglines()
        raise Exception(
            '{} never finished {}'.format(self._name, self._status))

    @staticmethod
    def get_free_port(nb=1):
        """Return free system ports that can be used by the daemon."""
        ports = []
        socks = []
        for _ in range(nb):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 0))
            socks.append(sock)
            ports.append(sock.getsockname()[1])
        for sock in socks:
            sock.close()
        return ports[0] if nb == 1 else ports

    def sanity_check(self):
        """Check that the daemon has no unexpected error messages in logs."""
