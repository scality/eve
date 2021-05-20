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

from buildbot.process.results import CANCELLED, FAILURE, SUCCESS

from tests.util.cluster import Cluster
from tests.util.yaml_factory import SingleCommandYaml, YamlFactory


class TestCluster(unittest.TestCase):
    def test1_cluster_start_stop(self):
        """Test cluster start and stop.

        Steps:
            - Start a cluster with 01 frontend and 01 backend.
            - Check that there are no errors in logs.
            - Stop it.

        """
        with Cluster() as cluster:
            cluster.sanity_check()

    def test2_bigger_cluster_start_stop(self):
        """Test addition of extra masters to a cluster.

        Steps:
            - Start a cluster with 01 frontend and 01 backend.
            - Add a frontend.
            - Add a backend.
            - Check that there are no errors in logs.
            - Stop it.

        """
        with Cluster() as cluster:
            cluster.add_master('frontend').start()
            cluster.add_master('backend').start()
            cluster.sanity_check()

    def test_simple_success(self):
        """Test a simple build success on a cluster.

        Steps:
            - Start a cluster with 01 frontend and 01 backend.
            - Force a job.
            - Check that all the expected steps are there.
            - Stop it.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push()
            cluster.api.force(branch=local_repo.branch)

            # Check bootstrap
            bootstrap_build = cluster.api.get_finished_build()
            self.assertEqual(bootstrap_build['results'], SUCCESS)
            bootstrap_steps = cluster.api.get_build_steps(bootstrap_build)
            step_names_and_descriptions = [(step['name'], step['state_string'])
                                           for step in bootstrap_steps]
            self.assertEqual(step_names_and_descriptions, [
                (u'worker_preparation', u'worker ready'),
                (u'set the bootstrap build number', u'Set'),
                (u'check index.lock', u"'test ! ...'"),
                (u'checkout git branch', u'update'),
                (u'cancel builds for commits that are not branch tips',
                 u'CancelNonTipBuild'),
                (u'set the master_builddir property', u'Set'),
                (u'get the product version',
                 u"property 'product_version' set"),
                (u'check the product version',
                 u"'echo 0.0.0 ...'"),
                (u'read eve/main.yml', u'uploading main.yml'),
                (u'get the commit short_revision',
                 u"property 'commit_short_revision' set"),
                (u'get the commit timestamp',
                 u"property 'commit_timestamp' set"),
                (u'set the artifacts name',
                 u"property 'artifacts_name' set"),
                (u'set the artifacts public url',
                 u"property 'artifacts_public_url' set"),
                (u'get the API version', u'Set'),
                (u'prepare 1 stage(s)', u'finished'),
                (u'trigger', u'triggered pre-merge')])

            # Check pre-merge
            premerge_build = cluster.api.get_finished_build(
                'pre-merge')
            self.assertEqual(premerge_build['results'], SUCCESS)
            premerge_steps = cluster.api.get_build_steps(premerge_build)
            step_names_and_descriptions = [(step['name'], step['state_string'])
                                           for step in premerge_steps]
            self.assertEqual(step_names_and_descriptions, [
                (u'worker_preparation', u'worker ready'),
                (u'prevent unuseful restarts', u"'[ $(expr ...'"),
                (u'set the artifacts private url',
                 u"property 'artifacts_private_url' set"),
                (u'Check worker OS distribution', u'finished'),
                (u'Set the current builder id', u'finished'),
                (u'Set the current build url', u'finished'),
                (u'extract steps from yaml', u'finished'),
                (u'shell', u"'exit 0'")])

            # Check build properties
            properties = cluster.api.getw(
                '/builds/{}'.format(bootstrap_build['buildid']),
                get_params={'property': '*'})
            from pprint import pprint
            pprint(properties)
            # TODO: imagine useful tests with build properties
            self.assertEqual(properties['properties']['stage_name'][0],
                             'bootstrap')
            self.assertEqual(properties['properties']['reason'][0],
                             'force build')
            self.assertEqual(properties['properties']['reason'][1],
                             'Force Build Form')

    def test_virtual_builder(self):
        """Test the virtual builder API.

        Steps:
            - Start a cluster with 01 frontend and 01 backend.
            - Force a job.
            - Wait for the build to end.
            - Ensure we can use the virtual_builder API.
            - Ensure the virtual_builder properties are well set.
            - Stop it.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push()
            cluster.api.force(branch=local_repo.branch)

            # Wait for the build to finish
            cluster.api.get_finished_build()
            premerge_build = cluster.api.get_finished_build('pre-merge')
            self.assertEqual(premerge_build['results'], SUCCESS)
            # Check build properties
            properties = cluster.api.get_build_properties(premerge_build)
            tags = [
                properties['git_host'][0],
                properties['git_owner'][0],
                properties['git_slug'][0],
                properties['stage_name'][0],
            ]

            self.assertEqual(properties['virtual_builder_name'][0],
                             'pre-merge')
            self.assertEqual(properties['virtual_builder_tags'][0], tags)

    def test_index_lock_failure(self):
        """Test a simple build failure on a cluster due to index.lock.

        Steps:
            - Start a cluster with 01 frontend and 01 backend.
            - Force a job.
            - Check that all the expected steps are there.
            - Stop it.

        """

        conf = {'MAX_LOCAL_WORKERS': '1'}
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push()

            for master_name in cluster._masters:
                if master_name.startswith('backend'):
                    base_path = cluster._masters[master_name]._base_path
                    git_path = ('{}/workers/lw000-test_suffix/bootstrap/'
                                'build/.git'.format(base_path))
                    local_repo.cmd('mkdir -p {}'.format(git_path))
                    local_repo.cmd('touch {}/index.lock'.format(git_path))

            cluster.api.force(branch=local_repo.branch)

            # Check bootstrap
            bootstrap_build = cluster.api.get_finished_build()
            self.assertEqual(bootstrap_build['results'], FAILURE)
            bootstrap_steps = cluster.api.get_build_steps(bootstrap_build)
            step_names_and_descriptions = [(step['name'], step['state_string'])
                                           for step in bootstrap_steps]
            self.assertEqual(step_names_and_descriptions, [
                (u'worker_preparation', u'worker ready'),
                (u'set the bootstrap build number', u'Set'),
                (u'check index.lock', u"'test ! ...' (failure)")])

    def test_worker_environ(self):
        """Test worker environment.

        Steps:
            - Spawn worker.
            - Check Eve environment variables are not setted in the worker.

        """
        conf = {'FOO': 'bar'}
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()

            local_repo.push(yaml=SingleCommandYaml('test -z "$FOO"'))
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'failure')
            child_build = \
                buildset.buildrequest.build.children[0].buildrequest.build
            self.assertEqual(child_build.first_failing_step.name, 'shell')
            self.assertEqual(child_build.first_failing_step.state_string,
                             "'test -z ...' (failure)")

    def test_force_parametrized_build(self):
        """Test forced build with parameters.

        Steps:
            - Spawn cluster with a parametrized force build scheduler.
            - Force a build with 2 parameters out of 5.
            - Check that the parameters are taken into account by reading
              the step's stdio log.

        """
        conf = {'FORCE_BUILD_PARAM_COUNT': '5'}
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(yaml=SingleCommandYaml(
                'echo The %(prop:color)s %(prop:vehicule)s'))
            buildset = cluster.api.force(
                branch=local_repo.branch,
                prop00_name='vehicule',
                prop00_value='submarine',
                prop01_name='color',
                prop01_value='yellow')

            self.assertEqual(buildset.result, 'success')
            child_build = buildset.buildrequest.build.children[
                0].buildrequest.build
            step = child_build.steps[-1]
            self.assertIn('The yellow submarine', step.rawlog('stdio'))

    def test_force_stage_build(self):
        """Test forced build with forced stage.

        Steps:
            - Spawn cluster with a force build scheduler.
            - Force a build with a given stage name.
            - Check that the correct stage is triggered.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(yaml=YamlFactory(
                branches={
                    'default': {'stage': 'default_stage'},
                },
                stages={
                    'default_stage': {
                        'worker': {'type': 'local'},
                        'steps': [{'ShellCommand': {'command': 'exit 1'}}],
                    },
                    'another_stage': {
                        'worker': {'type': 'local'},
                        'steps': [{'ShellCommand': {'command': 'echo "egg"'}}],
                    },
                }))
            buildset = cluster.api.force(
                branch=local_repo.branch,
                force_stage='another_stage')

            self.assertEqual(buildset.result, 'success')
            child_build = buildset.buildrequest.build.children[
                0].buildrequest.build
            step = child_build.steps[-1]
            self.assertIn('egg', step.rawlog('stdio'))

    def test_cancel_non_tip_build(self):
        """Check that commits that are not on tip of branch are cancelled.

        Steps:
        - commit twice on a branch
        - send a webhook to notify the first commit
        - verify that a build is launched and cancelled immediately

        """
        with Cluster() as cluster:
            repo = cluster.clone()
            repo.push(branch='spam', yaml=SingleCommandYaml('exit 0'))
            old_revision = repo.revision
            repo.push(branch='spam', yaml=SingleCommandYaml('exit 1'))
            cluster.webhook(repo, old_revision)

            build = cluster.api.get_finished_build()
            self.assertEqual(build['results'], CANCELLED)

    def test_bootstrap_and_master_properties(self):
        """Check the properties on bootstrap build.

        Steps:
        - submit a build via webhook
        - verify that the build runs correctly
        - check the expected properties are set

        """
        with Cluster() as cluster:
            repo = cluster.clone()
            repo.push(branch='spam', yaml=SingleCommandYaml('exit 0'))
            cluster.webhook(repo, repo.revision)

            build = cluster.api.get_finished_build()
            self.assertEqual(build['results'], SUCCESS)

            properties = cluster.api.get_build_properties(build)

            def check_prop(name, value=None, source=None):
                self.assertTrue(name in properties)
                if value:
                    self.assertEqual(properties[name][0], value)
                if source:
                    self.assertEqual(properties[name][1], source)

            check_prop('artifacts_name')
            check_prop('artifacts_public_url')
            check_prop('bootstrap', 1, 'set the bootstrap build number')
            check_prop('branch', 'spam', 'Build')
            check_prop('buildbot_version', '2.7.0')
            check_prop('builddir')
            check_prop('buildername', 'bootstrap', 'Builder')
            check_prop('buildnumber', 1, 'Build')
            check_prop('commit_short_revision')
            check_prop('commit_timestamp')
            check_prop('conf_path')
            check_prop('eve_api_version')
            check_prop('git_host', 'mock', 'Builder')
            check_prop('git_owner', 'repo_owner', 'Builder')
            check_prop('git_slug', 'test', 'Builder')
            check_prop('got_revision', repo.revision, 'Git')
            check_prop('master_builddir')
            check_prop('max_step_duration', 14400, 'Builder')
            check_prop('product_version', '0.0.0')
            check_prop('project', 'TEST', 'Build')
            check_prop('reason', 'branch updated', 'Scheduler')
            check_prop('repository', 'http://www.example.com/', 'Build')
            check_prop('revision', repo.revision, 'Build')
            check_prop('scheduler', 'bootstrap-scheduler', 'Scheduler')
            check_prop('stage_name', 'bootstrap', 'Builder')
            check_prop('start_time')
            check_prop('workername')

            master_build = cluster.api.get_finished_build('pre-merge')
            properties = cluster.api.get_build_properties(master_build)
            check_prop('artifacts_name')
            check_prop('artifacts_public_url')
            check_prop('bootstrap', 1, 'set the bootstrap build number')
            check_prop('bootstrap_reason', 'branch updated', 'BuildOrder')
            check_prop('branch', 'spam', 'Build')
            check_prop('buildbot_version', '2.7.0')
            check_prop('builddir')
            check_prop('buildername', 'local-test_suffix', 'Builder')
            check_prop('buildnumber', 1, 'Build')
            check_prop('commit_short_revision')
            check_prop('commit_timestamp')
            check_prop('conf_path')
            check_prop('eve_api_version')
            check_prop('git_host', 'mock', 'Builder')
            check_prop('git_owner', 'repo_owner', 'Builder')
            check_prop('git_slug', 'test', 'Builder')
            check_prop('got_revision', repo.revision, 'Git')
            check_prop('master_builddir')
            check_prop('max_step_duration', 14400, 'Builder')
            check_prop('product_version', '0.0.0')
            check_prop('project', 'TEST', 'Build')
            check_prop('reason', 'pre-merge (triggered by bootstrap)')
            check_prop('repository', 'http://www.example.com/', 'Build')
            check_prop('revision', repo.revision, 'Build')
            check_prop('scheduler', 'local-test_suffix', 'Scheduler')
            check_prop('stage_name', 'pre-merge', 'BuildOrder')
            check_prop('start_time')
            check_prop('workername')
