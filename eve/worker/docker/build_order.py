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

import buildbot
from buildbot.plugins import steps, util
from buildbot.process.properties import Interpolate
from buildbot.process.results import SKIPPED, SUCCESS


class DockerBuildOrder(util.BaseBuildOrder):
    """Base class representing a build to trigger on a Docker container.

    Scheduler, properties and docker config.

    """

    def setup_properties(self):
        super(DockerBuildOrder, self).setup_properties()

        self.properties['docker_volumes'] = self._worker.get('volumes', []) + [
            '{0}:{0}'.format('/var/run/docker.sock')
        ]

        # handle case of externally-supplied image
        if self._worker.get('image', False):
            self.properties['docker_image'] = Interpolate(
                self._worker['image'])
            return

        basename = self._worker.get('path', None)
        self.properties['worker_path'] = basename

        full_docker_path = '%s/build/%s' % (
            self.properties['master_builddir'],
            basename,
        )

        use_registry = bool(util.env.DOCKER_REGISTRY_URL)

        def should_build(step):
            if not use_registry:
                # No docker registry, always build
                return True
            properties = step.build.getProperties()
            image_exists = properties.getProperty(
                'exists_' + basename, False)
            return not image_exists

        if use_registry:
            self.preliminary_steps.append(steps.DockerComputeImageFingerprint(
                label=basename,
                context_dir=full_docker_path,
                hideStepIf=lambda results, s: results == SUCCESS
            ))

            image = Interpolate('{0}/{1}:%(prop:fingerprint_{1}:-)s'.format(
                util.env.DOCKER_REGISTRY_URL, basename))

            self.preliminary_steps.append(steps.DockerCheckLocalImage(
                label=basename,
                image=image,
                hideStepIf=lambda results, s: results == SUCCESS
            ))

            self.preliminary_steps.append(steps.DockerPull(
                label=basename,
                image=image,
                doStepIf=should_build,
                hideStepIf=lambda results, s: results == SUCCESS
            ))
        else:
            image = '%s-%06d' % (
                self.properties['worker_path'],
                self.properties['buildnumber'],
            )

        self.properties['docker_image'] = image

        common_args = {
            'label': basename,
            'image': image,
            'dockerfile': self._worker.get('dockerfile'),
            'workdir': full_docker_path,
            'build_args': {
                'BUILDBOT_VERSION': buildbot.version
            },
            'labels': {
                'eve.build.ts': '{0:.0f}'.format(time.time())
            }
        }

        self.preliminary_steps.append(steps.DockerBuild(
            flunkOnFailure=False,
            haltOnFailure=False,
            hideStepIf=lambda results, s: results == SUCCESS,
            doStepIf=should_build,
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

        self.preliminary_steps.append(steps.DockerBuild(
            name='[{0}] build retry'.format(basename)[0:49],
            is_retry=True,
            hideStepIf=lambda results, s: results == SKIPPED,
            doStepIf=is_prev_build_failed,
            **common_args
        ))
        # end of workaround

        if use_registry:
            self.preliminary_steps.append(steps.DockerPush(
                label=basename,
                image=image,
                doStepIf=should_build,
                hideStepIf=lambda results, s: results == SUCCESS
            ))
