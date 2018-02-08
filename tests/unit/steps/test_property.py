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
"""Unit tests of `eve.steps.property`."""

from __future__ import absolute_import

from buildbot.process.results import SKIPPED, SUCCESS
from buildbot.test.fake.remotecommand import ExpectShell
from buildbot.test.util import steps
from twisted.trial import unittest

from eve.steps.property import EveProperty, EvePropertyFromCommand


class TestEveProperty(steps.BuildStepMixin, unittest.TestCase):
    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def setupStep(self, property='my_prop', value='foo'):
        super(TestEveProperty, self).setupStep(
            EveProperty(property=property, value=value))

    def testBasic(self):
        self.setupStep()
        self.expectOutcome(SUCCESS)
        self.expectProperty('my_prop', 'foo', 'SetProperty')
        return self.runStep()

    def testSkipSetProperty(self):
        self.setupStep()
        self.properties.setProperty('my_prop', 'spam', 'Force Build Form')
        self.expectOutcome(SKIPPED)
        self.expectProperty('my_prop', 'spam', 'Force Build Form')
        return self.runStep()

    def testOverrideProperty(self):
        self.setupStep()
        self.properties.setProperty('my_prop', 'spam', 'someone')
        self.expectOutcome(SUCCESS)
        self.expectProperty('my_prop', 'foo', 'SetProperty')
        return self.runStep()


class TestEvePropertyFromCommand(steps.BuildStepMixin, unittest.TestCase):
    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def setupStep(self, property='my_prop', command=['ls'],
                  expect_command=True, stdout='foo'):
        super(TestEvePropertyFromCommand, self).setupStep(
            EvePropertyFromCommand(property=property,
                                   command=command))
        if expect_command:
            self.expectCommands(
                ExpectShell(workdir='wkdir', command=command)
                + ExpectShell.log('stdio', stdout=stdout)
                + 0)

    def testBasic(self):
        self.setupStep()
        self.expectOutcome(SUCCESS)
        self.expectProperty('my_prop', 'foo', 'SetPropertyFromCommand Step')
        return self.runStep()

    def testSkipSetProperty(self):
        self.setupStep(expect_command=False)
        self.properties.setProperty('my_prop', 'spam', 'Force Build Form')
        self.expectOutcome(SKIPPED)
        self.expectProperty('my_prop', 'spam', 'Force Build Form')
        return self.runStep()

    def testOverrideProperty(self):
        self.setupStep()
        self.properties.setProperty('my_prop', 'spam', 'someone')
        self.expectOutcome(SUCCESS)
        self.expectProperty('my_prop', 'foo', 'SetPropertyFromCommand Step')
        return self.runStep()
