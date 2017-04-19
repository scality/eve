# coding: utf-8

from unittest import TestCase

from tests.util.crossbar.crossbar import Crossbar


class TestCrossbar(TestCase):
    def test_start_and_stop(self):
        crossbar = Crossbar().start()
        assert "Router 'worker-001': transport 'transport-001' started" in \
               crossbar.loglines[-1]

        crossbar.stop()
        assert 'Shutting down node...' in crossbar.loglines[-1]
