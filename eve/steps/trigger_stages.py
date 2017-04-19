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
from buildbot.process.results import FAILURE, SUCCESS
from buildbot.steps.trigger import Trigger
from twisted.internet import defer

from ..util.build_order import BaseBuildOrder
from ..worker.docker.build_order import DockerBuildOrder
from ..worker.openstack.build_order import OpenStackBuildOrder


class TriggerStages(BuildStep):
    """Start a list of stages."""

    def __init__(self, stage_names, **kwargs_for_exec_trigger_stages):
        self.workers = {
            'local': (BaseBuildOrder, util.env.LOCAL_SCHEDULER_NAME),
            'docker': (DockerBuildOrder, util.env.DOCKER_SCHEDULER_NAME),
            'openstack': (OpenStackBuildOrder,
                          util.env.OPENSTACK_SCHEDULER_NAME)
        }

        self.stage_names = stage_names

        kwargs_for_exec_trigger_stages.setdefault('waitForFinish', True)
        self._kwargs_for_exec_trigger_stages = kwargs_for_exec_trigger_stages

        kwargs = {
            'name': 'prepare {0} stage(s)'.format(len(self.stage_names)),
            'hideStepIf': lambda results, s: results == SUCCESS,
            'haltOnFailure': True,
        }
        super(TriggerStages, self).__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        conf = self.getProperty('conf')

        preliminary_steps = OrderedDict()
        build_orders = []

        for stage_name in self.stage_names:
            stage = conf['stages'][stage_name]
            worker = stage['worker']

            build_order_class, scheduler_name = self.workers.get(
                worker['type'])

            if build_order_class is None:
                defer.returnValue(FAILURE)

            build_order = build_order_class(
                scheduler_name, util.env.GIT_REPO,
                stage_name, stage, worker, self
            )

            def set_property(result, build_order, propname):
                build_order.properties[propname] = result

            setprop_defers = []
            for propname, propvalue in build_order.properties.iteritems():
                setprop_defer = self.build.render(propvalue)
                setprop_defer.addCallback(set_property, build_order, propname)
                setprop_defers.append(setprop_defer)

            yield defer.gatherResults(setprop_defers)
            build_orders.append(build_order)

            for step in build_order.preliminary_steps:
                preliminary_steps[step] = ''

        self.build.addStepsAfterCurrentStep([
            ExecuteTriggerStages(
                build_orders, **self._kwargs_for_exec_trigger_stages
            )
        ])
        self.build.addStepsAfterCurrentStep(list(preliminary_steps))

        defer.returnValue(SUCCESS)


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

    def getSchedulersAndProperties(self):
        return [{
            'sched_name': build_order.scheduler,
            'props_to_set': build_order.properties,
            'unimportant': False
        } for build_order in self._build_orders]
