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

from tests.docker.cluster import DockerizedCluster as Cluster
from tests.util.yaml_factory import SingleCommandYaml


class TestSecrets(unittest.TestCase):
    def test_use_secrets(self):
        """Test a successful usage of vault secrets.

        Steps:
            - start a cluster with vault support
            - store a secret in its vault
            - check that the value is transmitted to a woker step by comparing
              its value : expected failure + expected success
            - stop the cluster
        """
        conf = {
            'VAULT_IN_USE': '1',
            'VAULT_FILE': 'path/to/file'
        }
        with Cluster(extra_conf=conf) as cluster:
            cluster.sanity_check()
            cluster.vault.write_secret(
                'path/to/file/secret_id', {'value': 'polichinelle'})
            self.assertEqual(
                cluster.vault.read_secret('path/to/file/secret_id'),
                {'value': 'polichinelle'}
            )

            for secret_value, expected_result in (('marionette', 'failure'),
                                                  ('polichinelle', 'success')):
                local_repo = cluster.clone()
                local_repo.push(yaml=SingleCommandYaml(
                    command='test $SECRET_ID = {}'.format(secret_value),
                    env={'SECRET_ID': '%(secret:secret_id)s'}))

                buildset = cluster.api.force(branch=local_repo.branch)
                self.assertEqual(buildset.result, expected_result)

                child_build = buildset.buildrequest.build.children[
                    0].buildrequest.build
                step = child_build.steps[-1]

                self.assertIn(
                    'SECRET_ID=<secret_id>', step.rawlog('stdio'))
                self.assertNotIn(
                    'SECRET_ID=%s' % secret_value, step.rawlog('stdio'))

            cluster.sanity_check()
