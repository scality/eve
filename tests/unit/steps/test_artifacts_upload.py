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
"""Unit tests of `eve.steps.artifacts`."""

from buildbot.test.util import config as configmixin
from buildbot.test.util import steps as testutil
from twisted.trial import unittest

from eve.steps.artifacts import Upload


class TestUpload(testutil.BuildStepMixin, unittest.TestCase,
                 configmixin.ConfigErrorsMixin):
    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def test_init_args_validity(self):
        """Test that an exception is raised for invalid argument."""
        self.assertRaisesConfigError(
            "Invalid argument(s) passed to RemoteShellCommand: ",
            lambda: Upload(source='ok', url=[], wrongArg1=1, wrongArg2='two'))

    def test_init_args(self):
        """Test that the constructor args are stored in the class."""
        upload_step = Upload('tmp', ['link1', 'link2'])
        self.assertEqual(upload_step._retry, (0, 1))
        self.assertEqual(upload_step._source, 'tmp')
        self.assertEqual(upload_step._urls, ['link1', 'link2'])
        self.assertEqual(upload_step.workdir, 'build/tmp')

    def test_retry_arg(self):
        """Test that the retry constructor arg is stored in the class."""
        upload_step = Upload('/tmp', ['link1', 'link2'], retry=(1, 2))
        self.assertEqual(upload_step._retry, (1, 2))
