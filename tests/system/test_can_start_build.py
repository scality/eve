
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

"""Testing canStartBuild method implemented in the builders config"""

import os
import time
import unittest
from tempfile import mkdtemp

from buildbot.process.results import SUCCESS

from tests.util.cluster import Cluster
from tests.util.yaml_factory import YamlFactory


class TestCanStartBuild(unittest.TestCase):
    def setUp(self):
        # Setting two backends to ensure this feature works with multiMaster
        self.cluster = Cluster(backends=2).start()
        self.local_repo = self.cluster.clone()

    def tearDown(self):
        self.cluster.stop()
        del self.cluster
        del self.local_repo

    def test_can_start_one_build(self):
        """Check behaviour with one simultaneous build."""
        file_path = os.path.join(mkdtemp(), 'file')
        command = """
            test ! -f {file_path} &&
            touch {file_path} &&
            test -f {file_path} &&
            sleep 5 &&
            rm {file_path}
        """.format(file_path=file_path)

        steps = [{'ShellCommand': {'command': command}}]
        branch = {'default': {'stage': 'pre-merge'}}
        stage = {'pre-merge': {
            'worker': {'type': 'local'},
            'steps': steps,
            'simultaneous_builds': 1
        }}

        self.local_repo.push(yaml=YamlFactory(branches=branch, stages=stage))
        for _ in range(8):
            self.cluster.api.force(branch=self.local_repo.branch)
        builds = self.cluster.api.get_builds()
        while len(builds) != 8:
            builds = self.cluster.api.get_builds()
        buildids = [b['buildid'] for b in builds]
        for buildid in buildids:
            build = self.cluster.api.get_build_for_id(buildid)
            build.wait_for_finish()
            self.assertEqual(build.result, 'success')

    def test_can_start_few_builds(self):
        """Check can start build method behaviour with N builds."""
        def get_running_builds(builds):
            return [
                build for build in builds if 'complete' not in build
                or build['complete'] is False
            ]
        total_builds = 8
        simultaneous_builds = 4
        command = "echo Ola Mundo!"
        steps = [{'ShellCommand': {'command': command}}]
        branch = {'default': {'stage': 'pre-merge'}}
        stage = {'pre-merge': {
            'worker': {'type': 'local'},
            'steps': steps,
            'simultaneous_builds': simultaneous_builds
        }}
        self.local_repo.push(yaml=YamlFactory(branches=branch, stages=stage))
        for _ in range(total_builds):
            self.cluster.api.force(branch=self.local_repo.branch)
        bootstrap = self.cluster.api.get_builds()

        # Wait for the pre-merge builder to be created
        for sleep in range(10):
            pre_merge = self.cluster.api.get(
                '/builders', {'name': 'pre-merge'})
            if sleep == 10 and not pre_merge:
                self.fail('pre-merge builder was not created')
            elif not pre_merge:
                time.sleep(sleep)
            else:
                pre_merge = get_running_builds(pre_merge)
                break
        while any(pre_merge) or any(bootstrap):
            assert len(pre_merge) <= simultaneous_builds
            pre_merge = get_running_builds(
                self.cluster.api.get_builds(builder='pre-merge'))
            bootstrap = get_running_builds(self.cluster.api.get_builds())
            # Just so that we don't spam the API
            time.sleep(0.5)

        # Retrieving all builds to check that they all ran successfully
        pre_merge = self.cluster.api.get_builds(builder='pre-merge')
        self.assertEqual(len(pre_merge), total_builds)
        for build in pre_merge:
            self.assertEqual(build['results'], SUCCESS)

    def test_can_start_build_error_handling(self):
        """Ensure string parameters are ignored."""
        steps = [{'ShellCommand': {'command': 'exit 0'}}]
        branch = {'default': {'stage': 'pre-merge'}}
        stage = {'pre-merge': {
            'worker': {'type': 'local'},
            'steps': steps,
            'simultaneous_builds': "string"
        }}
        self.local_repo.push(yaml=YamlFactory(branches=branch, stages=stage))
        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        buildset.wait_for_finish()
        self.assertEqual(buildset.result, 'success')
