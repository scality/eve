
# Copyright 2020 Scality
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

"""Test property steps"""

import unittest

from tests.util.cluster import Cluster
from tests.util.yaml_factory import YamlFactory


class TestProperties(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Start a cluster including a local Docker registry."""
        cls.cluster = Cluster().start()
        cls.local_repo = cls.cluster.clone()
        steps = [{'ShellCommand': {'command': 'exit 0'}}]
        branch = {'default': {'stage': 'pre-merge'}}
        stage = {'pre-merge': {
            'worker': {'type': 'local'},
            'steps': steps,
        }}
        cls.local_repo.push(yaml=YamlFactory(branches=branch, stages=stage))
        buildset = cls.cluster.api.force(branch=cls.local_repo.branch)
        build = buildset.buildrequest.build
        build.wait_for_finish()
        cls.premerge = build.children[0].buildrequest.build

        cls.premerge_builder = cls.cluster.api.get(
            '/builders', {'name': 'pre-merge'})[0]
        cls.exp_builderid = cls.premerge_builder.get('builderid')

    @classmethod
    def tearDownClass(cls):
        cls.cluster.sanity_check()
        cls.cluster.stop()

    def test_set_builder_id_implicit_call(self):
        """Test SetBuilderId and ensure the step is implicitly called."""
        builderid = self.premerge.properties.get('builderid')[0]
        assert builderid == self.exp_builderid

    def test_set_build_url_implicit_call(self):
        """Test SetBuildUrl and ensure the step is implicitly called."""
        buildurl = self.premerge.properties.get('buildurl')[0]
        buildnumber = self.premerge.properties.get('buildnumber')[0]
        exp_url = "{url}#builders/{builderid}/builds/{buildnumber}".format(
            url=self.cluster.external_url,
            builderid=self.exp_builderid,
            buildnumber=buildnumber
        )
        assert exp_url == buildurl
