from unittest import TestCase

from tests.util.cmd import cmd
from tests.util.daemon.daemon import Daemon


class SleepyDaemon(Daemon):
    """
    A fake daemon for testing purposes. It just sleeps for 1 hour.
    """
    _start_cmd = ['sleep', '3600']


class TestDaemon(TestCase):
    def test_get_free_port(self):
        """
        Test the the get_free_port() static method work correctly

        I suspect it to behave differently depending on the platform
        """
        free_ports = set()
        for _ in range(100):
            new_port = Daemon.get_free_port()
            if new_port in free_ports:
                raise Exception(
                    'Port {} has been given twice'.format(new_port))
            free_ports.add(new_port)

    def test_start_stop_sleepy_daemon(self):
        """
        Steps:
            - start a fake daemon and
            - check that it exists in `ps aux`
            - stop it
            - check that it disapeared from `ps aux`
        """
        fake_daemon = SleepyDaemon('sleep1H')
        fake_daemon.start()
        assert 'sleep 3600' in cmd('ps aux')
        fake_daemon.stop()
        assert 'sleep 3600' not in cmd('ps aux')
