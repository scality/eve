import os
import unittest

from tests.util.cluster import Cluster
from tests.util.yaml_factory import SingleCommandYaml

SUCCESS = 0


class TestCluster(unittest.TestCase):
    def test1_cluster_start_stop(self):
        cluster = Cluster().start()
        cluster.stop()

    def test2_bigger_cluster_start_stop(self):
        cluster = Cluster()
        cluster.start()
        master = cluster.add_master('frontend')
        master.start()
        master = cluster.add_master('backend')
        master.start()
        cluster.stop()

    def test3_simple_success(self):
        cluster = Cluster().start()
        local_repo = cluster.clone()

        local_repo.push()
        buildset = cluster.force(local_repo.branch)
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
        * Spawn worker
        * Check Eve environment variables are not setted in the worker
        """
        os.environ['FOO'] = 'bar'
        cluster = Cluster().start()
        local_repo = cluster.clone()

        local_repo.push(yaml=SingleCommandYaml('test -z "$FOO"'))
        buildset = cluster.force(local_repo.branch)
        assert buildset.result == 'failure'
        child_build = \
            buildset.buildrequest.build.children[0].buildrequest.build
        assert child_build.first_failing_step.name == 'shell'
        assert child_build.first_failing_step.state_string == \
            "'test -z ...' (failure)"
        cluster.stop()

    @unittest.skip('Test flaky on developers machine which need to be '
                   'investigated and fixed.')
    def test_lost_slave_recovery(self):
        """Ensures test can recover when slave is lost.

        Steps :
         * Launch the first job, that kills buildbot/container
         * The build shouldn't be retried and should fail
        """
        # self.commit_git('lost_slave_recovery')
        # self.notify_webhook()
        # self.get_build_result(expected_result='failure')
