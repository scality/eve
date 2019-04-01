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

from collections import OrderedDict

from buildbot.plugins import util
from buildbot.process.buildstep import BuildStep
from buildbot.process.properties import Properties
from buildbot.process.results import SUCCESS
from buildbot.steps.trigger import Trigger
from twisted.internet import defer

from ..util.build_order import BaseBuildOrder
from ..worker.docker.build_order import DockerBuildOrder
from ..worker.kubernetes.build_order import KubernetesPodBuildOrder
from ..worker.openstack_heat.build_order import HeatOpenStackBuildOrder
from .base import ConfigurableStepMixin


class TriggerStages(BuildStep, ConfigurableStepMixin):
    """Start a list of stages."""

    def __init__(self, stage_names, **kwargs_for_exec_trigger_stages):
        self.workers = {
            'local': (
                BaseBuildOrder,
                util.env.LOCAL_SCHEDULER_NAME),
            'docker': (
                DockerBuildOrder,
                util.env.DOCKER_SCHEDULER_NAME),
            'kube_pod': (
                KubernetesPodBuildOrder,
                util.env.KUBE_POD_SCHEDULER_NAME),
            'openstack': (
                HeatOpenStackBuildOrder,
                util.env.OPENSTACK_SCHEDULER_NAME),
        }

        self.stage_names = stage_names

        kwargs_for_exec_trigger_stages.setdefault('waitForFinish', True)
        self._kwargs_for_exec_trigger_stages = kwargs_for_exec_trigger_stages

        kwargs = {
            'name': 'prepare {0} stage(s)'.format(len(self.stage_names)),
            'hideStepIf': util.hideStepIfSuccess,
            'haltOnFailure': True,
        }
        super(TriggerStages, self).__init__(**kwargs)

    def run(self):
        conf = self.getEveConfig()
        preliminary_steps = OrderedDict()
        build_orders = []

        for stage_name in self.stage_names:
            stage = conf['stages'][stage_name]
            worker = stage['worker']

            try:
                build_order_class, scheduler_name = self.workers.get(
                    worker['type'])
            except TypeError:
                raise ValueError('%r is not a supported worker type' %
                                 worker['type'])

            build_order = build_order_class(
                scheduler_name, util.env.GIT_REPO,
                stage_name, stage, worker, self
            )

            build_orders.append(build_order)

            for step in build_order.preliminary_steps:
                preliminary_steps[step] = ''

        self.build.addStepsAfterCurrentStep([
            ExecuteTriggerStages(
                build_orders, **self._kwargs_for_exec_trigger_stages
            )
        ])
        self.build.addStepsAfterCurrentStep(list(preliminary_steps))

        return SUCCESS


class ExecuteTriggerStages(Trigger):
    """Execute simultaneously multiple build steps.

    It's a fake Trigger stage which run multiple BuildStep simultaneously.

    """

    def __init__(self, build_orders, *args, **kwargs):
        kwargs.update({
            'schedulerNames': ['foo']
        })
        super(ExecuteTriggerStages, self).__init__(*args, **kwargs)

        self._build_orders = build_orders

    @defer.inlineCallbacks
    def getSchedulersAndProperties(self):
        scheds_and_props = []

        def set_property(value, build_order, name, source):
            build_order.properties[name] = (value, source)

        for build_order in self._build_orders:
            # wait for properties from preliminary steps
            setprop_defers = []
            for name, (value, source) in build_order.properties.iteritems():
                setprop_defer = self.build.render(value)
                setprop_defer.addCallback(set_property,
                                          build_order,
                                          name,
                                          source)
                setprop_defers.append(setprop_defer)

            yield defer.gatherResults(setprop_defers)

            scheds_and_props.append({
                'sched_name': build_order.scheduler,
                'props_to_set': build_order.properties,
                'unimportant': False
            })
        defer.returnValue(scheds_and_props)

    def getCurrentSummary(self):
        if not self.triggeredNames:
            return {u'step': u'running'}
        return {u'step': u'triggered %s' % (
            u', '.join(bo.properties['stage_name'][0]
                       for bo in self._build_orders))}

    def createTriggerProperties(self, properties):
        return Properties.fromDict(properties)
