from unittest import TestCase

from tests.util.crossbar.crossbar import Crossbar


class TestCrossbar(TestCase):
    def test_start_and_stop(self):
        """
        Steps:
            - start crossbar
            - look for a line in the code to check if it completed its start
            - stop it
            - look for a line in the code to check if it completed its stop
        """
        crossbar = Crossbar().start()
        assert "Router 'worker-001': transport 'transport-001' started" in \
               crossbar.loglines[-1]

        crossbar.stop()
        assert 'Shutting down node...' in crossbar.loglines[-1]
