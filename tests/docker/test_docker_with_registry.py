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
from pprint import pprint

from buildbot.process.results import SUCCESS
from tests.docker.cluster import DockerizedCluster
from tests.util.cmd import cmd
from tests.util.yaml_factory import SingleCommandYaml


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start a cluster including a local Docker registry."""
        conf = {'DOCKER_REGISTRY_URL': 'mock'}
        cls.cluster = DockerizedCluster(extra_conf=conf).start()
        print('API URL: {}'.format(cls.cluster.api.api_url))
        cls.cluster.sanity_check()

    @classmethod
    def tearDownClass(cls):
        cls.cluster.sanity_check()
        cls.cluster.stop()

    def test_simple_build(self):
        """Test a simple build with registry support.

        Steps:
            - Check that the tag doesn't belong to the registry.
            - Build the project.
            - Check all steps for correctness, including image built
              and uploaded to the registry.
            - Check that the tagged image was added to the registry.
            - Build the project again.
            - Check all steps again, make sure image was not built,
              and reused straight from the local images.
            - Remove all local images.
            - Build the project again.
            - Check the image is pulled from the registry.

        """
        local_repo = self.cluster.clone()
        local_repo.push(
            yaml=SingleCommandYaml(
                'exit 0',
                worker={'type': 'docker',
                        'path': 'ubuntu-xenial-ctxt'}),
            dirs=[
                abspath(
                    join(__file__, pardir, 'contexts',
                         'ubuntu-xenial-ctxt'))
            ])
        self.cluster.api.force(branch=local_repo.branch)

        # Check bootstrap
        bootstrap = self.cluster.api.get_builder('bootstrap')
        bootstrap_build = self.cluster.api.get_finished_build(
            'bootstrap', timeout=180)
        self.assertEqual(bootstrap_build['results'], SUCCESS)
        bootstrap_steps = self.cluster.api.get_build_steps(bootstrap_build)
        step_names_and_descriptions = [(step['name'], step['state_string'])
                                       for step in bootstrap_steps]
        self.assertEqual(step_names_and_descriptions, [
            (u'set the bootstrap build number', u'Set'),
            (u'check index.lock', u"'test ! ...'"),
            (u'checkout git branch', u'update'),
            (u'cancel builds for commits that are not branch tips', u'CancelNonTipBuild'),  # noqa
            (u'set the master_builddir property', u'Set'),
            (u'get the product version', u"property 'product_version' set"),  # noqa
            (u'check the product version', u"'echo 0.0.0 ...'"),
            (u'read eve/main.yml', u'uploading main.yml'),
            (u'get the commit short_revision', u"property 'commit_short_revision' set"),  # noqa
            (u'get the commit timestamp', u"property 'commit_timestamp' set"),
            (u'set the artifacts name', u"property 'artifacts_name' set"),
            (u'set the artifacts public url', u"property 'artifacts_public_url' set"),  # noqa
            (u'get the API version', u'Set'),
            (u'prepare 1 stage(s)', u'finished'),
            (u'[ubuntu-xenial-ctxt_930a] fingerprint', u"Ran"),  # noqa
            (u'[ubuntu-xenial-ctxt_930a] look up', u"failed (1)"),  # noqa
            (u'[ubuntu-xenial-ctxt_930a] pull', u"failed (1)"),  # noqa
            (u'[ubuntu-xenial-ctxt_930a] build', u'Ran'),
            (u'[ubuntu-xenial-ctxt_930a] build retry', u'Ran (skipped)'),
            (u'[ubuntu-xenial-ctxt_930a] push', u'Ran'),
            (u'trigger', u'triggered pre-merge')])

        # Check build
        build = self.cluster.api.get_finished_build('pre-merge')
        self.assertEqual(build['results'], SUCCESS)
        steps = self.cluster.api.get_build_steps(build)
        step_names_and_descriptions = [(step['name'], step['state_string'])
                                       for step in steps]
        self.assertEqual(step_names_and_descriptions, [
            (u'prevent unuseful restarts', u"'[ $(expr ...'"),
            (u'set the artifacts private url',
             u"property 'artifacts_private_url' set"),
            (u'extract steps from yaml', u'finished'),
            (u'shell', u"'exit 0'")])

        # Check properties
        bootstrap_properties = self.cluster.api.getw(
            '/builds/{}'.format(bootstrap_build['buildid']),
            get_params={'property': '*'})
        pprint(bootstrap_properties)

        # now do the same build again, and check image is reused
        buildset = self.cluster.api.force(branch=local_repo.branch)
        buildrequestid = self.cluster.api.getw(
            '/buildrequests', {'buildsetid': buildset.bsid})['buildrequestid']

        bootstrap_build = self.cluster.api.getw('/builds', {
            'buildrequestid': buildrequestid,
            'builderid': bootstrap['builderid'],
            'results': SUCCESS
        })
        bootstrap_steps = self.cluster.api.get_build_steps(bootstrap_build)
        step_names_and_descriptions = [(step['name'], step['state_string'])
                                       for step in bootstrap_steps]
        self.assertEqual(step_names_and_descriptions, [
            (u'set the bootstrap build number', u'Set'),
            (u'check index.lock', u"'test ! ...'"),
            (u'checkout git branch', u'update'),
            (u'cancel builds for commits that are not branch tips', u'CancelNonTipBuild'),  # noqa
            (u'set the master_builddir property', u'Set'),
            (u'get the product version', u"property 'product_version' set"),
            (u'check the product version', u"'echo 0.0.0 ...'"),
            (u'read eve/main.yml', u'uploading main.yml'),
            (u'get the commit short_revision', u"property 'commit_short_revision' set"),  # noqa
            (u'get the commit timestamp', u"property 'commit_timestamp' set"),
            (u'set the artifacts name', u"property 'artifacts_name' set"),
            (u'set the artifacts public url', u"property 'artifacts_public_url' set"),  # noqa
            (u'get the API version', u'Set'),
            (u'prepare 1 stage(s)', u'finished'),
            (u'[ubuntu-xenial-ctxt_930a] fingerprint', u"Ran"),  # noqa
            (u'[ubuntu-xenial-ctxt_930a] look up', u"Ran"),  # noqa
            (u'[ubuntu-xenial-ctxt_930a] pull', u"Ran (skipped)"),  # noqa
            (u'[ubuntu-xenial-ctxt_930a] build', u'Ran (skipped)'),
            (u'[ubuntu-xenial-ctxt_930a] build retry', u'Ran (skipped)'),
            (u'[ubuntu-xenial-ctxt_930a] push', u'Ran (skipped)'),
            (u'trigger', u'triggered pre-merge')])

        # do the same build one last time, but erase the local image first
        build = self.cluster.api.getw('/builds', {
            'builderid': build['builderid'],
            'results': SUCCESS},
            expected_count=2
        )[1]
        image = self.cluster.api.getw(
            '/builds/{}'.format(build['buildid']),
            get_params={'property': '*'}
        )['properties']['docker_image'][0]

        cmd('docker rmi -f {}'.format(image))

        buildset = self.cluster.api.force(branch=local_repo.branch)
        buildrequestid = self.cluster.api.getw(
            '/buildrequests', {'buildsetid': buildset.bsid})['buildrequestid']

        bootstrap_build = self.cluster.api.getw('/builds', {
            'buildrequestid': buildrequestid,
            'builderid': bootstrap['builderid'],
            'results': SUCCESS
        })
        bootstrap_steps = self.cluster.api.get_build_steps(bootstrap_build)
        step_names_and_descriptions = [(step['name'], step['state_string'])
                                       for step in bootstrap_steps]
        self.assertEqual(step_names_and_descriptions, [
            (u'set the bootstrap build number', u'Set'),
            (u'check index.lock', u"'test ! ...'"),
            (u'checkout git branch', u'update'),
            (u'cancel builds for commits that are not branch tips', u'CancelNonTipBuild'),  # noqa
            (u'set the master_builddir property', u'Set'),
            (u'get the product version', u"property 'product_version' set"),  # noqa
            (u'check the product version', u"'echo 0.0.0 ...'"),
            (u'read eve/main.yml', u'uploading main.yml'),
            (u'get the commit short_revision', u"property 'commit_short_revision' set"),  # noqa
            (u'get the commit timestamp', u"property 'commit_timestamp' set"),  # noqa
            (u'set the artifacts name', u"property 'artifacts_name' set"),
            (u'set the artifacts public url', u"property 'artifacts_public_url' set"),  # noqa
            (u'get the API version', u'Set'),
            (u'prepare 1 stage(s)', u'finished'),
            (u'[ubuntu-xenial-ctxt_930a] fingerprint', u"Ran"),  # noqa
            (u'[ubuntu-xenial-ctxt_930a] look up', u"failed (1)"),  # noqa
            (u'[ubuntu-xenial-ctxt_930a] pull', u"Ran"),  # noqa
            (u'[ubuntu-xenial-ctxt_930a] build', u'Ran (skipped)'),
            (u'[ubuntu-xenial-ctxt_930a] build retry', u'Ran (skipped)'),
            (u'[ubuntu-xenial-ctxt_930a] push', u'Ran (skipped)'),
            (u'trigger', u'triggered pre-merge')])
