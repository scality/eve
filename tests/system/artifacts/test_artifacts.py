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

from tests.util.cluster import Cluster
from tests.util.yaml_factory import SingleCommandYaml


class TestArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conf = {
            'ARTIFACTS_PREFIX': 'aprefix-',
            'ARTIFACTS_PUBLIC_URL': 'https://foo.bar.baz'
        }
        cls.cluster = Cluster(extra_conf=conf).start()

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()
        del cls.cluster

    def setUp(self):
        self.local_repo = self.cluster.clone()

    def test_artifacts_properties(self):
        """Test that artifacts properties are well set."""
        self.local_repo.push(yaml=SingleCommandYaml('exit 0'))
        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        self.assertEqual(buildset.result, 'success')

        build = buildset.buildrequest.build
        child_buildsets = build.children
        self.assertEqual(len(child_buildsets), 1)
        child_build = child_buildsets[0].buildrequest.build
        self.assertEqual(child_build.result, 'success')

        short_hash = self.local_repo.cmd('git rev-parse --short HEAD')
        timestamp = self.local_repo.cmd('git log -1 --format=%cd '
                                        '--date="format-local:%y%m%d%H%M%S"')

        expected = 'mock:repo_owner:test:aprefix-0.0.0.r{}.{}.pre-merge.' \
                   '00000001'.format(timestamp.strip(), short_hash.strip())
        self.assertEqual(child_build.properties['artifacts_name'][0], expected)

        self.assertEqual(child_build.properties['artifacts_public_url'][0],
                         'https://foo.bar.baz/builds/' + expected)

        self.assertEqual(child_build.properties['artifacts_private_url'][0],
                         'http://artifacts/builds/' + expected)
