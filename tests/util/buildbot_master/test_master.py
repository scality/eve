# coding: utf-8

from unittest import TestCase

from tests.util.buildbot_master.buildbot_master import BuildbotMaster


class TestMaster(TestCase):
    def test_start_and_stop_master(self):
        master = BuildbotMaster(mode='standalone', git_repo='something')
        master.start()
        assert 'BuildMaster is running' in master.loglines[-1]
        master.stop()
        assert 'Server Shut Down.' in master.loglines[-1]
