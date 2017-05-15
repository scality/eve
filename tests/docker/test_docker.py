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

from tests.docker.cluster import DockerizedCluster
from tests.util.yaml_factory import PreMerge, SingleCommandYaml


class TestDockerCluster(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cluster = DockerizedCluster().start()
        print 'API URL:', cls.cluster.api.api_url
        cls.cluster.sanity_check()

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()

    def test1_bad_dockerfile(self):
        """Test the build fails when the Dockerfile is malformed.

        Steps:
            - Force a build with a bad Dockefile.
            - Check that the build fails.
            - Check that the failing step is the docker build step.

        """
        local_repo = self.cluster.clone()
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
        self.cluster.sanity_check()
        buildset = self.cluster.api.force(branch=local_repo.branch)
        assert buildset.result == 'failure'
        # Check that the failing build step is The good one
        fstep = buildset.buildrequest.build.first_failing_step
        assert fstep.name == 'build docker image from ' \
                             'bad-ubuntu-xenial-ctxt'

    def test2_simple_failure_in_docker(self):
        """Test that a command failure fails the whole build.

        Steps:
            - Force a build with a docker worker and a failing command.
            - Check that the build fails.
            - Check that the failing step is the failing command execution.

        """
        local_repo = self.cluster.clone()
        local_repo.push(
            yaml=SingleCommandYaml(
                'exit 1',
                worker={'type': 'docker',
                        'path': 'ubuntu-xenial-ctxt'}),
            dirs=[
                abspath(
                    join(__file__, pardir, 'contexts', 'ubuntu-xenial-ctxt'))
            ])
        self.cluster.sanity_check()
        buildset = self.cluster.api.force(branch=local_repo.branch)
        assert buildset.result == 'failure'
        child_build = \
            buildset.buildrequest.build.children[0].buildrequest.build
        assert child_build.first_failing_step.name == 'shell'
        assert child_build.first_failing_step.state_string == \
            "'exit 1' (failure)"

    def test3_simple_success_in_docker(self):
        """Test a successful build success with a docker worker.

        Steps:
            - Force a build with a docker worker and an 'exit 0' command.
            - Check that the build succeeds.

        """
        local_repo = self.cluster.clone()
        local_repo.push(
            yaml=SingleCommandYaml(
                'exit 0',
                worker={'type': 'docker',
                        'path': 'ubuntu-xenial-ctxt'}),
            dirs=[
                abspath(
                    join(__file__, pardir, 'contexts', 'ubuntu-xenial-ctxt'))
            ])
        self.cluster.sanity_check()
        buildset = self.cluster.api.force(branch=local_repo.branch)
        assert buildset.result == 'success'
        child_build = \
            buildset.buildrequest.build.children[0].buildrequest.build
        assert child_build.result == 'success'

    @unittest.skip('Flaky, need to understand how this works')
    def test_docker_build_label(self):
        """Test label on docker image exists."""
        local_repo = self.cluster.clone()
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

        self.cluster.sanity_check()
        buildset = self.cluster.api.force(branch=local_repo.branch)
        assert buildset.result == 'success'
        child_build = \
            buildset.buildrequest.build.children[0].buildrequest.build
        assert child_build.result == 'success'
        timestamp = int(child_build.properties['docker_image_timestamp'][0])
        assert timestamp >= time.time() - 120
        assert timestamp <= time.time()

    def test_use_different_dockerfile(self):
        """Test to build Docker image with a different Dockerfile.

        By default, ``docker build`` use the dockerfile named
        **/Dockerfile** inside the Docker context.
        We can use a different Dockerfile (see ``-f`` option of
        ``docker build`` command).

        """

        local_repo = self.cluster.clone()
        local_repo.push(
            yaml=SingleCommandYaml(
                'exit 0',
                worker={
                    'type': 'docker',
                    'path': 'use-different-dockerfile',
                    'dockerfile': 'foo/bar/Dockerfile.buz',
                }),
            dirs=[
                abspath(
                    join(__file__, pardir, 'contexts',
                         'use-different-dockerfile'))
            ])
        self.cluster.sanity_check()
        buildset = self.cluster.api.force(branch=local_repo.branch)
        assert buildset.result == 'success'
        child_build = \
            buildset.buildrequest.build.children[0].buildrequest.build
        assert child_build.result == 'success'

    def test_git_clone_in_docker_worker(self):
        """Test passwordless git clone works from within docker workers."""
        local_repo = self.cluster.clone()
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
                    'path': 'use-different-dockerfile',
                    'dockerfile': 'foo/bar/Dockerfile.buz',
                }),
            dirs=[
                abspath(
                    join(__file__, pardir, 'contexts',
                         'use-different-dockerfile'))
            ])
        self.cluster.sanity_check()
        buildset = self.cluster.api.force(branch=local_repo.branch)
        assert buildset.result == 'success'
        child_build = \
            buildset.buildrequest.build.children[0].buildrequest.build
        assert child_build.result == 'success'

    def test_docker_in_docker(self):
        """Test that we can launch a docker command inside a docker worker.

        Steps:
            - Substantiate a docker worker containing docker installation.
            - Launch a `docker ps` command.
            - Check that it succeeds.

        """

        local_repo = self.cluster.clone()
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
        self.cluster.sanity_check()
        buildset = self.cluster.api.force(branch=local_repo.branch)
        assert buildset.result == 'success'
        child_build = \
            buildset.buildrequest.build.children[0].buildrequest.build
        assert child_build.result == 'success'

    def test_use_premade_docker_img(self):
        """Test that we can build docker images on our own.

        Steps:
            - Substantiate a docker worker containing docker installation.
            - Launch a `docker build` command.
            - Launch a stage with the newly built image.
            - Check that it succeeds.

        """
        local_repo = self.cluster.clone()
        local_repo.push(
            yaml=abspath(
                join(__file__, pardir, 'yaml', 'use_premade_docker_image',
                     'main.yml')),
            dirs=[
                abspath(
                    join(__file__, pardir, 'contexts',
                         'ubuntu-xenial-with-docker-ctxt')),
                abspath(
                    join(__file__, pardir, 'contexts', 'ubuntu-xenial-ctxt'))
            ])

        self.cluster.sanity_check()
        buildset = self.cluster.api.force(branch=local_repo.branch)
        assert buildset.result == 'success'
        child_build = \
            buildset.buildrequest.build.children[0].buildrequest.build
        assert child_build.result == 'success'

    def test_use_premade_docker_img_p(self):
        """Test use of premade image but use property to store the image id."""

        local_repo = self.cluster.clone()
        local_repo.push(
            yaml=abspath(
                join(__file__, pardir, 'yaml',
                     'use_premade_docker_image_property', 'main.yml')),
            dirs=[
                abspath(
                    join(__file__, pardir, 'contexts',
                         'ubuntu-xenial-with-docker-ctxt')),
                abspath(
                    join(__file__, pardir, 'contexts', 'ubuntu-xenial-ctxt'))
            ])
        self.cluster.sanity_check()
        buildset = self.cluster.api.force(branch=local_repo.branch)
        assert buildset.result == 'success'
        child_build = \
            buildset.buildrequest.build.children[0].buildrequest.build
        assert child_build.result == 'success'

    def test_write_read_from_cache(self):
        """Test docker cache volumes.

        Steps:
            - Create a docker named volume and create a file into it.
            - Start another container and read a file from the same volume.

        """
        local_repo = self.cluster.clone()
        local_repo.push(
            yaml=abspath(
                join(__file__, pardir, 'yaml', 'write_read_from_cache',
                     'main.yml')),
            dirs=[
                abspath(
                    join(__file__, pardir, 'contexts', 'ubuntu-xenial-ctxt'))
            ])
        # self.cluster.sanity_check()
        buildset = self.cluster.api.force(branch=local_repo.branch)
        assert buildset.result == 'success'
