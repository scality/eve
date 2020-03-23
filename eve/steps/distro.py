# Copyright 2019 Scality
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
# Boston, MA  02110-1301, USA.import unittest

from buildbot.process.buildstep import BuildStep
from buildbot.steps.worker import CompositeStepMixin
from buildbot.process.results import SUCCESS
from twisted.logger import Logger
from twisted.internet import defer

"""Step regarding distributions."""


class SetWorkerDistro(BuildStep, CompositeStepMixin):
    """Build step designed to identify the linux OS distribution."""

    parms = BuildStep.parms + ['osReleaseFilePath']

    name = "SetWorkerDistro"
    osReleaseFilePath = '/etc/os-release'
    logger = Logger('eve.steps.distro')

    @defer.inlineCallbacks
    def run(self):
        distribution = {'ID': 'unknown', 'VERSION_ID': 'unknown'}
        self.logger.info('Starting distro check')
        osRelease = yield self.getFileContentFromWorker(self.osReleaseFilePath)
        if osRelease:
            for line in osRelease.splitlines():
                try:
                    k, v = line.strip().split("=")
                    distribution[k] = v.strip('""')
                except Exception:
                    pass
        self.setProperty(
            'distribution_id', distribution['ID'], 'SetWorkerDistro',
            runtime=True)
        self.setProperty(
            'distribution_version_id', distribution['VERSION_ID'],
            'SetWorkerDistro', runtime=True)
        defer.returnValue(SUCCESS)
