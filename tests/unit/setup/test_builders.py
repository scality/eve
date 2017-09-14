"""Unit tests of `eve.setup.builders`

Attributes:
    DumbWorker (namedtuple): structure to define a fake buildbot worker for
        builder tests.

"""

import collections
import unittest

from buildbot.plugins import util

import eve.setup.builders

DumbWorker = collections.namedtuple('DumbWorker', ['name'])


class TestSetupBuilders(unittest.TestCase):
    def setUp(self):
        util.env = util.load_env([
            ('DOCKER_BUILDER_NAME', 'foo'),
            ('OPENSTACK_BUILDER_NAME', 'bar'),
            ('MASTER_START_TIME', '9999', int),
            ('MICROSERVICE_GITCACHE_IN_USE', '0', int),
            ('MICROSERVICE_ARTIFACTS_IN_USE', '0', int),
        ])

    def test_triggerable_builder(self):
        builder_conf = eve.setup.builders.triggerable_builder(
            'foo', [DumbWorker(name='bar')])
        self.assertEquals(builder_conf.name, 'foo')
        self.assertEquals(builder_conf.workernames, ['bar'])
