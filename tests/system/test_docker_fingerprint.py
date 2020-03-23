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
"""This test suite checks Docker build fingerprint behavior."""

import unittest

from tempfile import mkdtemp
from tests.util.cluster import Cluster
from tests.util.yaml_factory import PreMerge


class TestDockerFingerPrint(unittest.TestCase):
    """Ensure that the fingerprint is computed as expected.

    When the dockerfile path is different from the context path we expect
    that the computed fingerprint will be different.

    Meaning that a change in the dockerfile OR a change in the context
    should trigger a rebuild of the docker image cache.
    """
    @classmethod
    def setUpClass(cls):
        cls.cluster = Cluster().start()
        print(cls.cluster.api.url)

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()
        del cls.cluster

    def setUp(self):
        self.local_repo = self.cluster.clone()

    def tearDown(self):
        del self.local_repo

    def test_docker_fingerprint(self):
        context = mkdtemp()
        command = """
            mkdir -p {context}/worker &&
            echo 'conf file' {context}/worker &&
            echo 'FROM ubuntu' > {context}/Dockerfile
        """.format(context=context)
        self.local_repo.push(
            yaml=PreMerge(steps=[
                {
                    'ShellCommand': {
                        'command': command
                    }
                },
                {
                    'DockerComputeImageFingerprint': {
                        'label': 'context_only',
                        'context_dir': '{context}/worker'.format(
                            context=context),
                        'name': 'fingerprint with context only',
                    }
                },
                {
                    'DockerComputeImageFingerprint': {
                        'label': 'context_and_dockerfile',
                        'context_dir': '{context}/worker'.format(
                            context=context),
                        'dockerfile': '{context}/Dockerfile'.format(
                            context=context),
                        'name': 'Fingerprint with context and dockerfile',
                    }
                }
            ])
        )
        buildset1 = self.cluster.api.force(branch=self.local_repo.branch)
        buildset1.wait_for_finish()
        self.assertEqual(buildset1.result, 'success')
        premerge1 = buildset1.buildrequest.build.children[0].buildrequest.build
        self.assertNotEqual(
            premerge1.properties['fingerprint_context_only'],
            premerge1.properties['fingerprint_context_and_dockerfile']
        )

        buildset2 = self.cluster.api.force(branch=self.local_repo.branch)
        buildset2.wait_for_finish()
        self.assertEqual(buildset2.result, 'success')
        premerge2 = buildset2.buildrequest.build.children[0].buildrequest.build
        self.assertEqual(
            premerge1.properties['fingerprint_context_only'],
            premerge2.properties['fingerprint_context_only'],
        )
        self.assertEqual(
            premerge1.properties['fingerprint_context_and_dockerfile'],
            premerge2.properties['fingerprint_context_and_dockerfile']
        )
