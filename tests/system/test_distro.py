
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

"""Test distro steps"""

import unittest

from tests.util.cluster import Cluster
from tests.util.yaml_factory import YamlFactory


class TestDistro(unittest.TestCase):
    def setUp(self):
        # Setting two backends to ensure this feature works with multiMaster
        self.cluster = Cluster(backends=1).start()
        self.local_repo = self.cluster.clone()

    def tearDown(self):
        self.cluster.stop()
        del self.cluster
        del self.local_repo

    def test_distro_implicit_call(self):
        """Test SetWorkerDistro and ensuring the step is implicitly called."""
        steps = [{'ShellCommand': {'command': 'exit 0'}}]
        branch = {'default': {'stage': 'pre-merge'}}
        stage = {'pre-merge': {
            'worker': {'type': 'local'},
            'steps': steps,
        }}
        self.local_repo.push(yaml=YamlFactory(branches=branch, stages=stage))
        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        build = buildset.buildrequest.build
        build.wait_for_finish()
        premerge = build.children[0].buildrequest.build
        # Just ensuring that the properties exists, and
        # that the default value has been overwritten
        assert premerge.properties['distribution_id'][0] != 'unknown'
        assert premerge.properties['distribution_version_id'][0] != 'unknown'

    def test_distro_non_existent_os_release_file(self):
        """Test SetWorkerDistro when os release file does not exist."""
        steps = [{'SetWorkerDistro': {'osReleaseFilePath': '/does/not/exist'}}]
        branch = {'default': {'stage': 'pre-merge'}}
        stage = {'pre-merge': {
            'worker': {'type': 'local'},
            'steps': steps,
        }}
        self.local_repo.push(yaml=YamlFactory(branches=branch, stages=stage))
        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        build = buildset.buildrequest.build
        build.wait_for_finish()
        premerge = build.children[0].buildrequest.build
        # Defaults to unknown when the os release file does not exist
        assert premerge.properties['distribution_id'][0] == 'unknown'
        assert premerge.properties['distribution_version_id'][0] == 'unknown'
