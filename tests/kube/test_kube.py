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
from os import pardir
from os.path import abspath, join

from tests.util.cluster import Cluster


class TestKube(unittest.TestCase):
    @unittest.skip('cannot run to completion until '
                   'we have an eve deployed in kube during tests')
    def test_simple_success_in_kube(self):
        """Test a successful build success with a kubernetes worker.

        Steps:
            - Force a build
            - Check that the build succeeds

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(
                    join(__file__, pardir, 'yaml', 'simple', 'main.yml')),
                dirs=[
                    abspath(join(__file__, pardir, 'contexts', 'simple'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            cluster.sanity_check()

    def test_incorrect_kube_yaml(self):
        """Test a build fails when incorrect yaml is provided to kube.

        Steps:
            - Force a build
            - Check that the build fails

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(
                    join(__file__, pardir, 'yaml', 'erroneous', 'main.yml')),
                dirs=[
                    abspath(join(__file__, pardir, 'contexts', 'simple'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'exception')
