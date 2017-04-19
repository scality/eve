"""Test module for eve.setup.builders module

Attributes:
    DumbWorker (namedtuple): structure to define a fake buildbot worker for
        builder tests.
"""
import collections
import unittest

import eve.setup.builders
from buildbot.plugins import util

DumbWorker = collections.namedtuple('DumbWorker', ['name'])


class SetupBuildersTest(unittest.TestCase):
    def setUp(self):
        util.env = util.load_env([
            ('DOCKER_BUILDER_NAME', 'foo'),
            ('GITCACHE_IN_USE', '0', int),
            ('MASTER_START_TIME', '9999', int),
        ])

    def test_triggerable_builder(self):
        """
        Test that the triggerable_builder function is run without throwing
        an exception and returns something different than None.
        """
        builder_conf = eve.setup.builders.triggerable_builder(
            'foo', [DumbWorker(name='bar')])
        self.assertEquals(builder_conf.name, 'foo')
        self.assertEquals(builder_conf.workernames, ['bar'])
