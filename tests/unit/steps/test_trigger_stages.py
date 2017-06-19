"""Unit tests of `eve.steps.trigger_stages`."""

import unittest

from buildbot.plugins import util

import eve.steps.trigger_stages


class StepsTriggerStages(unittest.TestCase):
    def setUp(self):
        util.env = util.load_env([
            ('LOCAL_SCHEDULER_NAME', 'foo'),
            ('DOCKER_SCHEDULER_NAME', 'bar'),
            ('OPENSTACK_SCHEDULER_NAME', 'foo')
        ])


class TestTriggerStages(unittest.TestCase):

    def setUp(self):
        util.env = util.load_env([
            ('LOCAL_SCHEDULER_NAME', 'foo'),
            ('DOCKER_SCHEDULER_NAME', 'bar'),
            ('OPENSTACK_SCHEDULER_NAME', 'foo')
        ])

    def test_init(self):
        ctx = eve.steps.trigger_stages.TriggerStages('stage_names')
        self.assertEquals(ctx.stage_names, 'stage_names')


class TestExecuteTriggerStages(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.trigger_stages.ExecuteTriggerStages('build_orders')
        self.assertEquals(ctx._build_orders, 'build_orders')