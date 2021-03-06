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

import time
import unittest
from os import pardir
from os.path import abspath, join

from buildbot.process.results import SUCCESS
from tests.docker.cluster import DockerizedCluster as Cluster
from tests.util.yaml_factory import PreMerge, SingleCommandYaml

from eve.util.hash import create_hash


class TestDockerCluster(unittest.TestCase):
    def test1_bad_dockerfile(self):
        """Test the build fails when the Dockerfile is malformed.

        Steps:
            - Force a build with a bad Dockefile.
            - Check that the build fails.
            - Check that the failing step is the docker build step.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=SingleCommandYaml(
                    'exit 0',
                    worker={'type': 'docker',
                            'path': 'bad-ubuntu-xenial-ctxt'}),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'bad-ubuntu-xenial-ctxt'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'failure')
            # Check that the failing build step is The good one
            fstep = buildset.buildrequest.build.first_failing_step
            self.assertEqual(fstep.name,
                             '[bad-ubuntu-xenial-ctxt_f532] build')
            cluster.sanity_check()

    def test2_simple_failure_in_docker(self):
        """Test that a command failure fails the whole build.

        Steps:
            - Force a build with a docker worker and a failing command.
            - Check that the build fails.
            - Check that the failing step is the failing command execution.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=SingleCommandYaml(
                    'exit 1',
                    worker={'type': 'docker',
                            'path': 'ubuntu-xenial-ctxt'}),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'ubuntu-xenial-ctxt'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'failure')
            child_build = \
                buildset.buildrequest.build.children[0].buildrequest.build
            self.assertEqual(child_build.first_failing_step.name, 'shell')
            self.assertEqual(child_build.first_failing_step.state_string,
                             "'exit 1' (failure)")
            cluster.sanity_check()

    def test3_simple_success_in_docker(self):
        """Test a successful build success with a docker worker.

        Steps:
            - Force a build with a docker worker and an 'exit 0' command.
            - Check that the build succeeds.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=PreMerge(
                    steps=[
                        {
                            'SetBootstrapProperty': {
                                'property': 'prop',
                                'value': 'value'
                            }
                        }, {
                            'SetBootstrapPropertyFromCommand': {
                                'property': 'cmd_prop',
                                'command': 'echo value'
                            }
                        }
                    ],
                    worker={
                        'type': 'docker',
                        'path': 'ubuntu-xenial-ctxt'
                    }),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'ubuntu-xenial-ctxt'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            bootstrap_properties = buildset.buildrequest.build.properties
            self.assertEqual(bootstrap_properties['prop'],
                             [u'value', u'SetBootstrapProperty'])
            self.assertEqual(bootstrap_properties['cmd_prop'],
                             [u'value', u'SetBootstrapPropertyFromCommand'])

            child_build = \
                buildset.buildrequest.build.children[0].buildrequest.build
            self.assertEqual(
                child_build.properties['bootstrap_reason'],
                [u'force build', u'BuildOrder'])
            self.assertEqual(child_build.result, 'success')
            hash = create_hash(child_build.properties['repository'][0],
                               child_build.properties['workername'][0])
            self.assertEqual(child_build.properties['worker_uuid'][0],
                             hash)
            cluster.sanity_check()

    @unittest.skip('Flaky, need to understand how this works')
    def test_docker_build_label(self):
        """Test label on docker image exists."""
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=PreMerge(
                    steps=[{
                        'SetPropertyFromCommand': {
                            'property':
                            'docker_image_timestamp',
                            'command':
                            "docker inspect -f "
                            "'{{ index .Config.Labels \"eve.build.ts\" }}'"
                            " %(prop:docker_image)s",
                        }
                    }],
                    worker={
                        'type': 'docker',
                        'path': 'ubuntu-xenial-with-docker-ctxt'
                    }),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'ubuntu-xenial-with-docker-ctxt'))
                ])

            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            child_build = \
                buildset.buildrequest.build.children[0].buildrequest.build
            self.assertEqual(child_build.result, 'success')
            timestamp = int(
                child_build.properties['docker_image_timestamp'][0])
            self.assertGreaterEqual(timestamp, time.time() - 120)
            self.assertLessEqual(timestamp, time.time())
            cluster.sanity_check()

    def test_use_different_dockerfile(self):
        """Test to build Docker image with a different Dockerfile.

        By default, ``docker build`` use the dockerfile named
        **/Dockerfile** inside the Docker context.
        We can use a different Dockerfile (see ``-f`` option of
        ``docker build`` command).

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=SingleCommandYaml(
                    'exit 0',
                    worker={
                        'type': 'docker',
                        'path': 'use-different-dockerfile/foo',
                        'dockerfile':
                            'use-different-dockerfile/Dockerfile.buz',
                    }),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'use-different-dockerfile'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            child_build = \
                buildset.buildrequest.build.children[0].buildrequest.build
            self.assertEqual(child_build.result, 'success')
            cluster.sanity_check()

    def test_git_clone_in_docker_worker(self):
        """Test passwordless git clone works from within docker workers."""
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=PreMerge(
                    steps=[{
                        'Git': {
                            'name': 'git pull',
                            'repourl': '%(prop:git_reference)s',
                            'shallow': True,
                            'retryFetch': True,
                            'haltOnFailure': True,
                        }
                    }],
                    worker={
                        'type': 'docker',
                        'path': 'use-different-dockerfile/foo',
                        'dockerfile':
                            'use-different-dockerfile/Dockerfile.buz',
                    }),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'use-different-dockerfile'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            child_build = \
                buildset.buildrequest.build.children[0].buildrequest.build
            self.assertEqual(child_build.result, 'success')
            cluster.sanity_check()

    def test_docker_in_docker(self):
        """Test that we can launch a docker command inside a docker worker.

        Steps:
            - Substantiate a docker worker containing docker installation.
            - Launch a `docker ps` command.
            - Check that it succeeds.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=SingleCommandYaml(
                    'docker ps',
                    worker={
                        'type': 'docker',
                        'path': 'ubuntu-xenial-with-docker-ctxt'
                    }),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'ubuntu-xenial-with-docker-ctxt'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            child_build = \
                buildset.buildrequest.build.children[0].buildrequest.build
            self.assertEqual(child_build.result, 'success')
            cluster.sanity_check()

    def test_use_premade_docker_img(self):
        """Test that we can build docker images on our own.

        Steps:
            - Substantiate a docker worker containing docker installation.
            - Launch a `docker build` command.
            - Launch a stage with the newly built image.
            - Check that it succeeds.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(
                    join(__file__, pardir, 'yaml', 'use_premade_docker_image',
                         'main.yml')),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'ubuntu-xenial-with-docker-ctxt')),
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'ubuntu-xenial-ctxt'))
                ])

            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            child_build = \
                buildset.buildrequest.build.children[0].buildrequest.build
            self.assertEqual(child_build.result, 'success')
            cluster.sanity_check()

    def test_use_premade_docker_img_p(self):
        """Test use of premade image but use property to store the image id."""
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(
                    join(__file__, pardir, 'yaml',
                         'use_premade_docker_image_property', 'main.yml')),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'ubuntu-xenial-with-docker-ctxt')),
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'ubuntu-xenial-ctxt'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            child_build = \
                buildset.buildrequest.build.children[0].buildrequest.build
            self.assertEqual(child_build.result, 'success')
            cluster.sanity_check()

    def test_write_read_from_cache(self):
        """Test docker cache volumes.

        Steps:
            - Create a docker named volume and create a file into it.
            - Start another container and read a file from the same volume.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(
                    join(__file__, pardir, 'yaml', 'write_read_from_cache',
                         'main.yml')),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'ubuntu-xenial-ctxt'))
                ])
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            cluster.sanity_check()

    def test_long_step_name(self):
        """Test that the build succeeds when a long step name is provided.

        Include some interpolated variables in the step name to check
        that they are correctly handled.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=PreMerge(steps=[{
                    'ShellCommand': {
                        'name': '%(prop:buildername)s This is a long step '
                                '%(prop:buildername)s and very short command; '
                                'Lorem ipsum amet, dis sem wisi ligula conu '
                                'lectus. Hendrerit ut diam. Massa magna, '
                                'nunc pede tempor quisque nullam magna. '
                                'Arcu et suspendisse nam venenatis, wisi '
                                'metus at arcu nisl massa magna, nulla '
                                'felis, urna aenean a quam penatibus turpis '
                                'fringilla, sed a mattis volutpat '
                                'pellentesque sint est. Ridiculus orci '
                                'molestie sagittis justo non. ',
                        'command': 'exit 0'}}]))
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')

            # Check pre-merge step
            premerge_build = cluster.api.get_finished_build(
                'pre-merge')
            self.assertEqual(premerge_build['results'], SUCCESS)
            premerge_steps = cluster.api.get_build_steps(premerge_build)
            step_names_and_descriptions = [(step['name'], step['state_string'])
                                           for step in premerge_steps]
            self.assertEqual(step_names_and_descriptions, [
                (u'prevent unuseful restarts', u"'[ $(expr ...'"),
                (u'set the artifacts private url',
                 u"property 'artifacts_private_url' set"),
                (u'Check worker OS distribution', u'finished'),
                (u'Set the current builder id', u'finished'),
                (u'Set the current build url', u'finished'),
                (u'extract steps from yaml', u'finished'),
                (u'local-test_suffix This is a long step ',
                    u"'exit 0'")])
            cluster.sanity_check()

    def test_docker_hook_workers_on(self):
        """Test the property docker_hook is set when required.

        Steps:
            - set the DOCKER_HOOK_... environment to contain worker.
            - Force a build.
            - Check that the build succeeds.
            - Check that bootstrap does not have the property.
            - Check that the docker build has the property set to True.

        """
        conf = {
            'DOCKER_HOOK_IN_USE': '1',
            'DOCKER_HOOK_VERSION': '1.2.3',
            'DOCKER_HOOK_WORKERS': 'riri;ubuntu-xenial-with-docker-ctxt;plop',
        }
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=SingleCommandYaml(
                    'exit 0',
                    worker={
                        'type': 'docker',
                        'path': 'ubuntu-xenial-with-docker-ctxt'
                    }),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'ubuntu-xenial-with-docker-ctxt'))
                ])
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            self.assertTrue('docker_hook' not in
                            buildset.buildrequest.build.properties)

            child_build = \
                buildset.buildrequest.build.children[0].buildrequest.build
            self.assertEqual(child_build.result, 'success')
            self.assertEqual(child_build.properties['docker_hook'][0], '1.2.3')
            cluster.sanity_check()

    def test_docker_hook_workers_off(self):
        """Test the property docker_hook is set when required.

        Steps:
            - set the DOCKER_HOOK_... environment to invalid data.
            - Force a build.
            - Check that the build succeeds.
            - Check that bootstrap does not have the property.
            - Check that the docker build has the property set to False.

        """
        conf = {
            'DOCKER_HOOK_IN_USE': '1',
            'DOCKER_HOOK_VERSION': '1.2.3',
            'DOCKER_HOOK_WORKERS': 'ri;not-ubuntu-xenial-with-docker-ctxt;pl',
        }
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=SingleCommandYaml(
                    'exit 0',
                    worker={
                        'type': 'docker',
                        'path': 'ubuntu-xenial-with-docker-ctxt'
                    }),
                dirs=[
                    abspath(
                        join(__file__, pardir, 'contexts',
                             'ubuntu-xenial-with-docker-ctxt'))
                ])
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            self.assertTrue('docker_hook' not in
                            buildset.buildrequest.build.properties)

            child_build = \
                buildset.buildrequest.build.children[0].buildrequest.build
            self.assertEqual(child_build.result, 'success')
            self.assertTrue('docker_hook' not in child_build.properties)
            cluster.sanity_check()

    def test_docker_invalid_image_name(self):
        """Test a docker build with a non existent docker image.

        Steps:
            - Set a bad docker image.
            - Force a build.
            - Ensure that the build status is on 'exception'.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=SingleCommandYaml(
                    'exit 0',
                    worker={'type': 'docker',
                            'image': 'bad-docker-image'})
            )
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'exception')

    # Couldn't reproduce EVE-1013 with sqlite (system tests)
    # so this tests is purposely setup in the docker testsuite
    # as it actually communicates with a mysql database.
    def test_big_yaml_file(self):
        """Test a docker build with a big yaml file.

        Steps:
            - Setup a big yaml file.
            - Force a build.
            - Ensure that the build status is on 'success'.

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=SingleCommandYaml('echo %s' % ('a' * 100000)))
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
