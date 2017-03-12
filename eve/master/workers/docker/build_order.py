import time

import buildbot
from buildbot.process.properties import Interpolate
from buildbot.process.results import SKIPPED

from utils.build_order import BaseBuildOrder
from workers.docker.build_step import DockerBuild


class DockerBuildOrder(BaseBuildOrder):
    """Base class representing a build to trigger on a Docker container
    (Scheduler, properties and docker config)
    """

    def setup_properties(self):
        super(DockerBuildOrder, self).setup_properties()

        self.properties['docker_volumes'] = self._worker.get('volumes', []) + [
            '{0}:{0}'.format('/var/run/docker.sock')
        ]

        self.properties['worker_path'] = self._worker.get('path')
        if self.properties['worker_path'] is None:
            self.properties['docker_image'] = Interpolate(
                self._worker['image'])
            return

        full_docker_path = '%s/build/%s' % (
            self.properties['master_builddir'],
            self.properties['worker_path'],
        )
        self.properties['docker_image'] = '%s-%06d' % (
            self.properties['worker_path'],
            self.properties['buildnumber'],
        )

        common_args = {
            'image': self.properties['docker_image'],
            'dockerfile': self._worker.get('dockerfile'),
            'workdir': full_docker_path,
            'build_args': {
                'BUILDBOT_VERSION': buildbot.version
            },
            'labels': {
                'eve.build.ts': '{0:.0f}'.format(time.time())
            }
        }

        self.preliminary_steps.append(DockerBuild(
            name='build docker image from {0}'.format(
                self.properties['worker_path']
            ),
            flunkOnFailure=False,
            haltOnFailure=False,
            **common_args
        ))

        # Workaround EVE-215
        # The previous docker build could fail because:
        # - the dockerfile is incorrect
        # - the remote sources are unavailable
        # - or we hit EVE-215, and the previous image in cache
        #   is not reliable
        # In all cases, try again once and ignore cached images (nocache)

        def is_prev_build_failed(step):
            properties = step.build.getProperties()
            prec_failed_image = properties.getProperty('DockerBuildFailed', '')
            return prec_failed_image == step.image

        self.preliminary_steps.append(DockerBuild(
            name='docker build retry from {0}'.format(
                self.properties['worker_path']
            ),
            is_retry=True,
            hideStepIf=lambda results, s: results == SKIPPED,
            doStepIf=is_prev_build_failed,
            **common_args
        ))
        # end of workaround
