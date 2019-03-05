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

from os import path

from buildbot.plugins import util
from buildbot.process.properties import Interpolate


class DockerBuildOrder(util.BaseDockerBuildOrder):
    """Base class representing a build to trigger on a Docker container.

    Scheduler, properties and docker config.

    """

    def setup_properties(self):
        super(DockerBuildOrder, self).setup_properties()

        memory = (self._worker.get('memory', None))
        self.properties['docker_memory'] = (memory, 'DockerBuildOrder')

        volumes = (self._worker.get('volumes', [])
                   + ['{0}:{0}'.format('/var/run/docker.sock')])
        self.properties['docker_volumes'] = (volumes, 'DockerBuildOrder')

        # handle case of externally-supplied image
        if self._worker.get('image', False):
            self.properties['docker_image'] = (
                Interpolate(self._worker['image']),
                'DockerBuildOrder')
            return

        worker_path = self._worker.get('path', None)
        self.properties['worker_path'] = (worker_path, 'DockerBuildOrder')

        if util.env.DOCKER_HOOK_IN_USE:
            if worker_path in util.env.DOCKER_HOOK_WORKERS.split(';'):
                self.properties['docker_hook'] = (
                    util.env.DOCKER_HOOK_VERSION,
                    'DockerBuildOrder')

        dockerfile = self._worker.get('dockerfile', None)
        self.properties['docker_image'] = (
            self._build_image(path.basename(worker_path), worker_path,
                              dockerfile),
            'DockerBuildOrder',
        )
