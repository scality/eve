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
"""Allow eve to use docker workers."""

from subprocess import STDOUT, CalledProcessError, check_output

from buildbot.interfaces import LatentWorkerCannotSubstantiate
from buildbot.plugins import util
from buildbot.process.properties import Property
from buildbot.worker.latent import AbstractLatentWorker
from twisted.internet import defer, threads
from twisted.logger import Logger


class EveDockerLatentWorker(AbstractLatentWorker):
    """Eve version on the DockerLatentWorker.

    Improved version of DockerLatentWorker using the docker command line client
    instead of docker-py which was the cause of multiple dead locks.

    """

    quarantine_timeout = quarantine_initial_timeout = 5 * 60
    quarantine_max_timeout = 60 * 60

    logger = Logger('eve.workers.EveDockerLatentWorker')
    instance = None

    def __init__(self, name, password, image, master_fqdn, pb_port,
                 max_memory, max_cpus, **kwargs):
        # pylint: disable=too-many-arguments
        self.image = image
        self.master_fqdn = master_fqdn
        self.pb_port = pb_port
        self.max_memory = max_memory
        self.max_cpus = max_cpus
        kwargs.setdefault('build_wait_timeout', 0)
        kwargs.setdefault('keepalive_interval', None)
        AbstractLatentWorker.__init__(self, name, password, **kwargs)

    @defer.inlineCallbacks
    def start_instance(self, build):
        if self.instance is not None:
            raise ValueError('instance active')
        repository = build.getProperty('repository')
        uuid = util.create_hash(repository, self.name)
        build.setProperty("worker_uuid", uuid, "Build")
        image = yield build.render(self.image)
        memory = build.getProperty('docker_memory')
        volumes = build.getProperty('docker_volumes')
        docker_hook_version = build.getProperty('docker_hook', None)
        buildnumber = yield build.render(Property('bootstrap'))
        res = yield threads.deferToThread(self._thd_start_instance, image,
                                          memory, volumes, buildnumber,
                                          docker_hook_version)
        defer.returnValue(res)

    def _thd_start_instance(self, image, memory, volumes, buildnumber,
                            docker_hook_version):

        self.logger.info('Checking if %r docker image exist.' % image)
        if not self.docker('images', '--format', '{{.Repository}}', image):
            self.logger.error('%r image not found.' % image)
            raise LatentWorkerCannotSubstantiate(
                'Image %s not found on docker host' % image
            )

        cmd = [
            'run',
            '--privileged',
            '--env', 'BUILDMASTER=%s' % self.master_fqdn,
            '--env', 'BUILDMASTER_PORT=%s' % self.pb_port,
            '--env', 'WORKERNAME=%s' % self.name,
            '--env', 'WORKERPASS=%s' % self.password,
            '--label', 'buildnumber=%s' % buildnumber,
            '--detach',
            '--cpus=%s' % self.max_cpus
        ]

        if memory:
            if (util.convert_to_bytes(memory) >
                    util.convert_to_bytes(self.max_memory)):
                self.logger.error('Can not request %s RAM (max allowed %s).' %
                                  (memory, self.max_memory))
                raise LatentWorkerCannotSubstantiate(
                    'Can not request %s RAM (max allowed is %s).' %
                    (memory, self.max_memory)
                )
            cmd.append('--memory=%s' % memory)
        else:
            cmd.append('--memory=%s' % self.max_memory)

        cmd.extend(['--volume=%s' % volume for volume in volumes])

        if docker_hook_version:
            cmd.append('--label=docker_hook=%s' % docker_hook_version)

        cmd.append(image)

        try:
            self.instance = self.docker(*cmd)
        except CalledProcessError:
            raise LatentWorkerCannotSubstantiate(
                'Docker run: CMD failed to start or died shortly after'
            )

        self.logger.debug('Container created, Id: %s...' % self.instance)
        return [self.instance, image]

    def stop_instance(self, fast=False):
        assert not fast  # unused parameter, we cannot remove it (PEP8)
        if self.instance is None:
            return defer.succeed(None)
        instance = self.instance
        self.instance = None
        return threads.deferToThread(self._thd_stop_instance, instance)

    def _thd_stop_instance(self, instance):
        self.logger.debug('Stopping container %s...' % instance)
        self.docker('kill', instance)
        self.docker('wait', instance)
        self.docker('rm', '--volumes', instance)
        self.logger.debug('Container %s stopped successfully.' % instance)

    def docker(self, *args):
        """Call the docker client binary.

        It calls the `docker` command with the arguments given as a parameter
        and logs exceptions if any.

        Args:
            *args: Arguments to pass to `docker`.

        Returns:
            str: The output of the commmand (stderr + stdout).

        """
        cmd = ['docker'] + list(args)
        self.logger.debug('::RUNNING::{}'.format(' '.join(cmd)))
        return check_output(cmd, stderr=STDOUT).strip()
