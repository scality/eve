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

from buildbot.config import BuilderConfig
from buildbot.plugins import steps, util
from buildbot.process.factory import BuildFactory
from buildbot.util.logger import Logger
from twisted.internet import defer

log = Logger()


@defer.inlineCallbacks
def canStartBuild(builder, wfb, request):
    """Ensure we can run simultaneous builds on a stage."""
    log.debug('Checking if we can start...')
    simultaneous_builds = request.properties.getProperty('simultaneous_builds')
    if simultaneous_builds:
        try:
            simultaneous_builds = int(simultaneous_builds)
        except ValueError:
            # When the object can be casted into an int ignore the value
            return True
        log.debug('%d simultaneous builds are allowed' % simultaneous_builds)
        name = request.properties.getProperty(
            'virtual_builder_name',
            builder.name
        )
        builderid = yield builder.getBuilderIdForName(name)
        log.debug('Checking running builds for %s...' % name)
        builds = yield builder.master.db.builds.getBuilds(
            builderid=builderid,
            complete=False
        )
        builds = [x for x in builds if x['results'] is None]
        running_builds = len(builds)
        log.debug('%d builds are running for %s' % (running_builds, name))
        return simultaneous_builds > running_builds
    return True


def triggerable_builder(builder_name, workers):
    factory = BuildFactory()
    factory.addStep(steps.CancelOldBuild(name='prevent unuseful restarts'))
    factory.addStep(steps.SetArtifactsPrivateURL(
        builder_name == util.env.OPENSTACK_BUILDER_NAME))
    # Add property regarding linux OS distribution
    factory.addStep(steps.SetWorkerDistro(
        name='Check worker OS distribution',
        hideStepIf=True,
        flunkOnFailure=False
    ))
    # Extract steps from conf
    factory.addStep(steps.StepExtractor(
        name='extract steps from yaml',
        hideStepIf=util.hideStepIfSuccess
    ))

    return BuilderConfig(
        name=builder_name,
        workernames=[w.name for w in workers],
        factory=factory,
        collapseRequests=False,
        canStartBuild=canStartBuild)
