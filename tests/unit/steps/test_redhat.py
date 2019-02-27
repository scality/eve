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
# Boston, MA  02110-1301, USA.

from buildbot.process.results import SKIPPED, SUCCESS
from buildbot.test.fake.remotecommand import ExpectShell
from buildbot.test.util import steps
from twisted.trial import unittest

from eve.steps.redhat import UnregisterRedhat
from eve.util.redhat import isRedhat


class TestUnregisterRedhat(steps.BuildStepMixin, unittest.TestCase):

    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def test_success(self):
        self.setupStep(UnregisterRedhat())

        self.expectCommands(
            ExpectShell(workdir='wkdir',
                        command='sudo subscription-manager unregister')
            + 0
        )
        self.expectOutcome(
            result=SUCCESS,
            state_string="Unregistered from Red Hat Customer Portal"
        )
        return self.runStep()

    def test_skipped(self):
        command = "rpm -qa | grep -qE '^redhat-release.+'"
        self.setupStep(UnregisterRedhat(doStepIf=isRedhat))
        self.expectCommands(
            ExpectShell(workdir='/', command=command) + 1
        )
        self.expectOutcome(result=SKIPPED)
        return self.runStep()
