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
"""This test suite checks end-to-end operation of EVE."""

import unittest
from os import pardir
from os.path import abspath, join

from tests.util.cluster import Cluster


class TestJunit(unittest.TestCase):
    def test_junit_step(self):  # pylint: disable=too-many-statements
        """Test customized JUnitShellCommand step with OK tests.

        Steps:
            - Spawn worker.
            - Have various commands create JUnit reports and parse them.

        """
        cluster = Cluster().start()
        cluster.sanity_check()

        local_repo = cluster.clone()
        parent = abspath(join(__file__, pardir))
        yaml = join(parent, 'main.yml')
        reports_dir = join(parent, 'reports')
        local_repo.push(yaml=yaml, dirs=(reports_dir, ))
        cluster.sanity_check()
        buildset = cluster.api.force(branch=local_repo.branch)
        self.assertEqual(buildset.result, 'failure')
        child_build = \
            buildset.buildrequest.build.children[0].buildrequest.build

        results = [(step.name, step.state_string, step.result)
                   for step in child_build.steps]
        expected = [
            (
                u'prevent unuseful restarts',
                u"'[ $(expr ...'",
                'success'
            ),
            (
                u'set the artifacts private url',
                u"property 'artifacts_private_url' set",
                'success'
            ),
            (
                u'Check worker OS distribution',
                u'finished',
                u'success'
            ),
            (
                u'extract steps from yaml',
                u'finished',
                'success'
            ),
            (
                u'git pull',
                u'update',
                'success'),
            (
                u'SetProperty',
                u'Set',
                'success'
            ),
            (
                u'single report with one pass',
                u'T:1 E:0 F:0 S:0',
                'success'
            ),
            (
                u'three reports with lots of pass',
                u'T:217 E:0 F:0 S:0',
                # u'T:2134 E:0 F:0 S:108',
                'success'
            ),
            (
                u'no files in directory',
                u'no test results found',
                'warnings'
            ),
            (
                u'missing report directory',
                u'no test results found',
                'warnings'
            ),
            (
                u'single report with invalid data',
                u'no test results found',
                'warnings'
            ),
            (
                u'report with invalid data along valid report',
                u'T:1 E:0 F:0 S:0',
                'success'
            ),
            (
                u'single report with invalid extension',
                u'no test results found',
                'warnings'
            ),
            (
                u'report with failures and successful command',
                u'FAIL: toto.tests.sample.test_sample.test_sample',
                'failure'
            ),
            (
                u'report with no failures and failed command',
                u'T:1 E:0 F:0 S:0',
                'failure'
            ),
            (
                u'report with failures',
                u'FAIL: toto.tests.sample.test_sample.test_sample',
                'failure'
            ),
            (
                u'report with errors',
                u'ERROR: supervisor.test_01_deployment.TestGenericDeployment.'
                u'test_supervisor_configuration[os_trusty]',
                'failure'
            ),
            (
                u'report with skips',
                u'T:144 E:0 F:0 S:24',
                'success'),
            (
                u'report with both errors and failures',
                u'ERROR: supervisor.test_01_deployment.TestGenericDeployment.'
                u'test_supervisor_configuration[os_trusty]',
                'failure'
            ),
            (
                u'report with one xfail and one xpass',
                u'T:2 E:0 F:0 S:2',
                'success'
            ),
            (
                u'undeclared report directory and a pass',
                u'no test results found',
                'warnings'
            ),
            (
                u'undeclared report directory and a fail',
                u'no test results found',
                'failure'
            ),
            (
                u'test report paths with success',
                u'T:1 E:0 F:0 S:0',
                'success'
            ),
            (
                u'test report paths with failure',
                u'FAIL: toto.tests.sample.test_sample.test_sample',
                'failure'
            ),
            (
                u'test report paths with success and failure',
                u'FAIL: toto.tests.sample.test_sample.test_sample',
                'failure'
            ),
            (
                u'test report paths with success and failure in same',
                u'FAIL: toto.tests.sample.test_sample.test_sample',
                'failure'
            ),
            (
                u'test report paths only uploading success',
                u'T:1 E:0 F:0 S:0',
                'success'
            ),
            (
                u'test report paths only uploading failure',
                u'FAIL: toto.tests.sample.test_sample.test_sample',
                'failure'
            ),
            (
                u'test report paths without list',
                u'T:1 E:0 F:0 S:0',
                'success'
            ),
            (
                u'test report paths with non existing file',
                u'no test results found',
                'warnings'
            ),
            (
                u'test report paths with non matching glob',
                u'no test results found',
                'warnings'
            )
        ]

        self.assertEqual(results, expected)
        cluster.stop()
