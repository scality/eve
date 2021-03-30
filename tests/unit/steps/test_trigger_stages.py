"""Unit tests of `eve.steps.trigger_stages`."""

from buildbot.plugins import util
from buildbot.process.results import SUCCESS
from buildbot.test.unit.test_steps_trigger import FakeTriggerable
from buildbot.test.util import steps
from twisted.internet import defer
from twisted.trial import unittest

from eve.steps.trigger_stages import ExecuteTriggerStages, TriggerStages


class FakeBuildOrder(object):
    def __init__(self, scheduler, properties):
        self.scheduler = scheduler
        self.properties = properties


class FakeSchedulerManager(object):
    def __init__(self, scheduler):
        self.namedServices = {scheduler: FakeTriggerable(scheduler)}


class TestTriggerStages(unittest.TestCase):
    def setUp(self):
        util.env = util.load_env([
            ('LOCAL_SCHEDULER_NAME', 'foo'),
            ('DOCKER_SCHEDULER_NAME', 'bar'),
            ('KUBE_POD_SCHEDULER_NAME', 'baz'),
            ('OPENSTACK_SCHEDULER_NAME', 'foo')
        ])

    def test_init(self):
        ctx = TriggerStages('stage_names')
        self.assertEqual(ctx.stage_names, 'stage_names')


class TestExecuteTriggerStages(steps.BuildStepMixin, unittest.TestCase):
    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def setupStep(self, scheduler='foo', properties=None):
        properties = properties or {}
        self.scheduler = scheduler
        self.exp_trigger = {}
        super(TestExecuteTriggerStages, self).setupStep(
            ExecuteTriggerStages([FakeBuildOrder(scheduler, properties)]))

        self.master.scheduler_manager = FakeSchedulerManager(self.scheduler)

    @defer.inlineCallbacks
    def runStep(self):
        d = super(TestExecuteTriggerStages, self).runStep()
        yield d
        for name, sched in self.master.scheduler_manager.namedServices.items():
            self.assertEqual(sched.triggered_with,
                             self.exp_trigger[name])

    def expectTriggeredWith(self, scheduler='foo', waited_for=False,
                            properties=None):
        properties = properties or {}
        self.exp_trigger[scheduler] = (waited_for, [], properties)

    def test_init(self):
        ctx = ExecuteTriggerStages('build_orders')
        self.assertEqual(ctx._build_orders, 'build_orders')

    def test_set_properties(self):
        self.setupStep(properties={'stage_name': ('because', 'here'),
                                   'x': (1, 'there')})
        self.expectOutcome(result=SUCCESS,
                           state_string='triggered because')
        self.expectTriggeredWith(properties={'stage_name': ('because', 'here'),
                                             'x': (1, 'there')})
        return self.runStep()
