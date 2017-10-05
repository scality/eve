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
"""This test suite checks end-to-end operation of the patcher."""

import os
import unittest

from tests.util.cluster import Cluster
from tests.util.yaml_factory import PreMerge, SingleCommandYaml


class TestPatcher(unittest.TestCase):
    def test_patcher_stage_match(self):
        """Test that a stage skip is taken into account."""

        PATCHER_DATA = {
            'skip_stages': [
                'pre-merge',
            ],
        }
        conf = {'PATCHER_FILE_PATH': 'patcher.yml'}
        with Cluster(extra_conf=conf) as cluster:

            for master in cluster._masters.values():
                master.add_conf_file(
                    yaml_data=PATCHER_DATA,
                    filename=os.path.join(master._base_path, 'patcher.yml')
                )

            repo = cluster.clone()

            repo.push(branch='other-branch', yaml=PreMerge(steps=[
                {'ShellCommand': {'name': 'step1', 'command': 'exit 0'}},
            ]))
            buildset = cluster.api.force(branch=repo.branch)
            self.assertEqual(buildset.result, 'cancelled')

            cluster.sanity_check()

    def test_patcher_branch_match(self):
        """Test that a branch skip is taken into account."""

        PATCHER_DATA = {
            'skip_branches': [
                'spam',
                'egg',
            ],
        }
        conf = {'PATCHER_FILE_PATH': 'patcher.yml'}
        with Cluster(extra_conf=conf) as cluster:

            for master in cluster._masters.values():
                master.add_conf_file(
                    yaml_data=PATCHER_DATA,
                    filename=os.path.join(master._base_path, 'patcher.yml')
                )

            repo = cluster.clone()

            repo.push(branch='spam-branch', yaml=SingleCommandYaml('exit 0'))
            buildset = cluster.api.force(branch=repo.branch)
            self.assertEqual(buildset.result, 'cancelled')

            cluster.sanity_check()

    def test_patcher_branch_no_match(self):
        """Test that a step skip is taken into account."""

        PATCHER_DATA = {
            'skip_branches': [
                'spam',
                'egg',
            ],
            'skip_steps': [
                'step1',
                'step3',
            ],
            'skip_stages': [
                'bacon',
            ],
        }
        conf = {'PATCHER_FILE_PATH': 'patcher.yml'}
        with Cluster(extra_conf=conf) as cluster:

            for master in cluster._masters.values():
                master.add_conf_file(
                    yaml_data=PATCHER_DATA,
                    filename=os.path.join(master._base_path, 'patcher.yml')
                )

            repo = cluster.clone()

            repo.push(branch='other-branch', yaml=PreMerge(steps=[
                {'ShellCommand': {'name': 'step1', 'command': 'exit 0'}},
                {'ShellCommand': {'name': 'step2', 'command': 'exit 0'}},
                {'ShellCommand': {'name': 'step3', 'command': 'exit 0'}},
            ]))

            buildset = cluster.api.force(branch=repo.branch)
            self.assertEqual(buildset.result, 'success')

            # Check pre-merge
            premerge_build = cluster.api.get_finished_build(
                'local-test_suffix')
            premerge_steps = cluster.api.get_build_steps(premerge_build)
            step_names_and_descriptions = [(step['name'], step['state_string'])
                                           for step in premerge_steps]
            self.assertEqual(step_names_and_descriptions, [
                (u'prevent unuseful restarts', u"'[ $(expr ...'"),
                (u'set the artifacts private url',
                 u"property 'artifacts_private_url' set"),
                (u'extract steps from yaml', u'finished'),
                (u'step1', u'Temporarily disabled (skipped)'),
                (u'step2', u"'exit 0'"),
                (u'step3', u'Temporarily disabled (skipped)')
            ])

            cluster.sanity_check()
