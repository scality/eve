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

import unittest

from tests.util.cluster import Cluster
from tests.util.yaml_factory import PreMerge


class TestStepTimeout(unittest.TestCase):

    def test_step_timeout_property(self):
        """Test configurable step timeouts property."""
        conf = {'MAX_STEP_DURATION': '9128'}
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=PreMerge(
                    steps=[{
                        'ShellCommand': {
                            'command': 'echo good',
                            'timeout': '%(prop:max_step_duration)s',
                        }
                    }]))
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')

            build = buildset.buildrequest.build
            child = build.children[0].buildrequest.build
            self.assertEqual(child.result, 'success')
            self.assertEqual(child.properties['max_step_duration'][0], 9128)

    def test_step_timeout_for_real(self):
        """Test short step timeouts."""
        conf = {'MAX_STEP_DURATION': '1400'}
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=PreMerge(
                    steps=[{
                        'ShellCommand': {
                            'command': 'sleep 10',
                            'timeout': '1',
                        }
                    }]))
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'failure')

    def test_step_timeout_invalid_type(self):
        """Test configurable step timeouts with invalid value."""
        conf = {'MAX_STEP_DURATION': '1400'}
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=PreMerge(
                    steps=[{
                        'ShellCommand': {
                            'command': 'echo bad',
                            'timeout': 'a string',
                        }
                    }]))
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'exception')

    def test_step_timeout_too_long(self):
        """Test configurable step timeouts too high."""
        conf = {'MAX_STEP_DURATION': '1400'}
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=PreMerge(
                    steps=[{
                        'ShellCommand': {
                            'command': 'echo bad',
                            'timeout': 10000,
                        }
                    }]))
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'exception')
