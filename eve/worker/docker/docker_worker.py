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

import time
from subprocess import STDOUT, CalledProcessError, check_output

from buildbot.process.properties import Property
from buildbot.worker.latent import AbstractLatentWorker
from twisted.internet import defer, threads
from twisted.logger import Logger


class EveDockerLatentWorker(AbstractLatentWorker):
    """Eve version on the DockerLetentWorker.

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
        self.master_fqdn = master_fqdn,
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
        image = yield build.render(self.image)
        volumes = build.getProperty('docker_volumes')
        docker_hook_version = build.getProperty('docker_hook', None)
        buildnumber = yield build.render(Property('bootstrap'))
        res = yield threads.deferToThread(self._thd_start_instance, image,
                                          volumes, buildnumber,
                                          docker_hook_version)
        defer.returnValue(res)

    def _thd_start_instance(self, image, volumes, buildnumber,
                            docker_hook_version):
        cmd = [
            'run',
            '--privileged',
            '--env', 'BUILDMASTER=%s' % self.master_fqdn,
            '--env', 'BUILDMASTER_PORT=%s' % self.pb_port,
            '--env', 'WORKERNAME=%s' % self.name,
            '--env', 'WORKERPASS=%s' % self.password,
            '--label', 'buildnumber=%s' % buildnumber,
            '--detach',
            '--memory=%s' % self.max_memory,
            '--cpus=%s' % self.max_cpus
        ]

        cmd.extend(['--volume=%s' % volume for volume in volumes])

        if docker_hook_version:
            cmd.append('--label=docker_hook=%s' % docker_hook_version)

        cmd.append(image)
        self.instance = self.docker_invoke(*cmd)
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
        self.docker_invoke('kill', instance)
        self.docker_invoke('wait', instance)
        self.docker_invoke('rm', '--volumes', instance)
        self.logger.debug('Container %s stopped successfully.' % instance)

    def docker_invoke(self, *args):
        """Call the docker client binary.

        It calls the `docker` command with the arguments given as a parameter
        and logs exceptions if any.

        Args:
            *args: Arguments to pass to `docker`.

        Returns:
            str: The output of the commmand (stderr + stdout).

        """
        cmd = ['docker']
        cmd.extend(args)
        cmd_shell = ' '.join(cmd)
        try:
            self.logger.debug('::RUNNING::{}'.format(cmd_shell))
            res = check_output(cmd, stderr=STDOUT).strip()
            return res
        except CalledProcessError as exception:
            time.sleep(5)  # avoid a fast loop in case of failure
            raise RuntimeError('CalledProcessError: {} *** OUTPUT: {}'.format(
                cmd_shell,
                exception.output
            ))
