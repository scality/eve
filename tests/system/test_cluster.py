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

import os
import unittest

from tests.util.cluster import Cluster
from tests.util.yaml_factory import SingleCommandYaml

SUCCESS = 0


class TestCluster(unittest.TestCase):
    def test1_cluster_start_stop(self):
        """Test cluster start and stop.

        Steps:
            - Start a cluster with 01 frontend and 01 backend.
            - Check that there are no errors in logs.
            - Stop it.

        """
        cluster = Cluster().start()
        cluster.sanity_check()
        cluster.stop()

    def test2_bigger_cluster_start_stop(self):
        """Test addition of extra masters to a cluster.

        Steps:
            - Start a cluster with 01 frontend and 01 backend.
            - Add a frontend.
            - Add a backend.
            - Check that there are no errors in logs.
            - Stop it.

        """
        cluster = Cluster()
        cluster.start()
        master = cluster.add_master('frontend')
        master.start()
        master = cluster.add_master('backend')
        master.start()
        cluster.sanity_check()
        cluster.stop()

    def test3_simple_success(self):
        """Test a simple build success on a cluster.

        Steps:
            - Start a cluster with 01 frontend and 01 backend.
            - Force a job.
            - Check that all the expected steps are there.
            - Stop it.

        """
        cluster = Cluster().start()
        local_repo = cluster.clone()

        local_repo.push()
        buildset = cluster.api.force(branch=local_repo.branch)
        buildrequestid = cluster.api.getw(
            '/buildrequests', {'buildsetid': buildset.bsid})['buildrequestid']

        print cluster.api.url
        bootstrap = cluster.api.getw('/builders', {
            'name': 'bootstrap',
        })['builderid']

        bootstrap_build = cluster.api.getw('/builds', {
            'buildrequestid': buildrequestid,
            'builderid': bootstrap,
            'results': SUCCESS
        })
        local_builder = cluster.api.getw(
            '/builders', {'name': 'local-test_suffix'})['builderid']

        local_build = cluster.api.getw(
            '/builds', {'builderid': local_builder,
                        'results': SUCCESS})
        bootstrap_steps = cluster.api.getw(
            '/builds/{}/steps'.format(bootstrap_build['buildid']),
            expected_count=21)

        step_names_and_descriptions = [(step['name'], step['state_string'])
                                       for step in bootstrap_steps]
        assert step_names_and_descriptions == \
            [

                (u'checkout git branch', u'update'),
                (u'Cancel builds for commits that are not branch tips',
                 u'CancelNonTipBuild'),
                (u'setting the master_builddir property', u'Set'),
                (u'check if any steps should currently be patched',
                 u'finished (skipped)'),
                (u'get the git host', u'Set'),
                (u'get the git owner', u'Set'),
                (u'get the repository name', u'Set'),
                (u'get the product version',
                 u"property 'product_version' set"),
                (u'read eve/main.yml', u'uploading main.yml'),
                (u'get the commit short_revision',
                 u"property 'commit_short_revision' set"),
                (u'get the commit timestamp',
                 u"property 'commit_timestamp' set"),
                (u'get the pipeline name', u'Set'),
                (u'get the b4nb', u'Set'),
                (u'set the artifacts base name',
                 u"property 'artifacts_base_name' set"),
                (u'set the artifacts name',
                 u"property 'artifacts_name' set"),
                (u'set the artifacts local reverse proxy', u'Set'),
                (u'set the artifacts private url',
                 u"property 'artifacts_private_url' set"),
                (u'set the artifacts public url',
                 u"property 'artifacts_public_url' set"),
                (u'get the API version', u'Set'),
                (u'prepare 1 stage(s)', u'finished'),
                (u'trigger', u'triggered local-test_suffix')
            ]
        local_steps = cluster.api.getw(
            '/builds/{}/steps'.format(local_build['buildid']),
            expected_count=3)
        step_names_and_descriptions = [(step['name'], step['state_string'])
                                       for step in local_steps]
        assert step_names_and_descriptions == \
            [
                (u'prevent unuseful restarts', u"'[ $(expr ...'"),
                (u'extract steps from yaml', u'finished'),
                (u'shell', u"'exit 0'")
            ]

        bootstrap_properties = cluster.api.getw(
            '/builds/{}'.format(bootstrap_build['buildid']),
            get_params={'property': '*'})
        from pprint import pprint
        pprint(bootstrap_properties)
        # TODO: imagine useful tests with build properties
        cluster.stop()

    def test_worker_environ(self):
        """Test worker environment.

        Steps:
            - Spawn worker.
            - Check Eve environment variables are not setted in the worker.

        """
        os.environ['FOO'] = 'bar'
        cluster = Cluster().start()
        local_repo = cluster.clone()

        local_repo.push(yaml=SingleCommandYaml('test -z "$FOO"'))
        buildset = cluster.api.force(branch=local_repo.branch)
        assert buildset.result == 'failure'
        child_build = \
            buildset.buildrequest.build.children[0].buildrequest.build
        assert child_build.first_failing_step.name == 'shell'
        assert child_build.first_failing_step.state_string == \
            "'test -z ...' (failure)"
        cluster.stop()

    def test_force_parametrized_build(self):
        """Test forced build with parameters.

        Steps:
        * Spawn cluster with a parametrized force build scheduler
        * Force a build with 2 parameters out of 5
        * Check that the parameters are taken into account by reading the step
          stdio log.
        """
        os.environ['FORCE_BUILD_PARAM_COUNT'] = '5'
        cluster = Cluster().start()
        local_repo = cluster.clone()
        local_repo.push(yaml=SingleCommandYaml(
            'echo The %(prop:color)s %(prop:vehicule)s'))
        buildset = cluster.api.force(
            branch=local_repo.branch,
            prop00_name='vehicule',
            prop00_value='submarine',
            prop01_name='color',
            prop01_value='yellow')

        assert buildset.result == 'success'
        child_build = buildset.buildrequest.build.children[
            0].buildrequest.build
        step = child_build.steps[-1]
        assert 'The yellow submarine' in step.rawlog('stdio')
        cluster.stop()
