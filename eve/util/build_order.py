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

from hashlib import sha1
from time import time

import buildbot
from buildbot.plugins import steps, util
from buildbot.process.properties import Interpolate
from twisted.internet import defer


class BaseBuildOrder(object):
    """Class representing a build to trigger (Scheduler and properties)."""

    def __init__(self, scheduler, git_repo, stage_name, stage,
                 worker, parent_step):
        self.git_repo = git_repo
        self.scheduler = scheduler
        self._stage_name = stage_name
        self._stage = stage
        self._worker = worker
        self._parent_step = parent_step

        self.properties = {}
        self.preliminary_steps = []

        self.setup_properties()

    def setup_properties(self):
        """Set additional properties."""
        self.properties.update(self._parent_step.getProperties().properties)
        self.properties.setdefault(
            'bootstrap_reason',
            (self.properties['reason'][0], 'BuildOrder'))
        stage_name = self.properties.get('stage_name', ['unknown'])[0]
        self.properties.update({
            'stage_name': (self._stage_name, 'BuildOrder'),
            'reason': ('%s (triggered by %s)' % (
                self._stage_name, stage_name), 'BuildOrder'),
            'git_reference': (self.git_repo, 'BuildOrder'),
            'git_repo': (self.git_repo, 'BuildOrder'),
        })


class BaseDockerBuildOrder(BaseBuildOrder):
    """Base class representing a build using docker images."""

    def _build_image(self, image_name, context_dir, dockerfile=None):
        """Ensure given docker image is available for worker.

        This method computes the fingerprint from the provided docker context
        and either pulls the image or builds it.
        If a registry is available, the image will be pushed to it.

        Returns the generated image name.

        """
        full_context_dir = '%s/build/%s' % (
            self.properties['master_builddir'][0],
            context_dir,
        )
        if dockerfile:
            dockerfile = '%s/build/%s' % (
                self.properties['master_builddir'][0],
                dockerfile,
            )

        # image name is image_name + hash of path to avoid collisions
        basename = "{0}_{1}".format(
            image_name,
            sha1(context_dir.encode('utf-8')).hexdigest()[:4])

        use_registry = bool(util.env.DOCKER_REGISTRY_URL)

        def should_build(step):
            if not use_registry:
                # No docker registry, always build
                return True
            image_exists = step.getProperty(
                'exists_' + basename, False)
            return not image_exists

        if use_registry:
            self.preliminary_steps.append(
                steps.DockerComputeImageFingerprint(
                    label=basename,
                    context_dir=full_context_dir,
                    hideStepIf=util.hideStepIfSuccess))

            image = Interpolate('{0}/{1}:%(prop:fingerprint_{1})s'.format(
                util.env.DOCKER_REGISTRY_URL, basename))

            self.preliminary_steps.append(steps.DockerCheckLocalImage(
                label=basename,
                image=image,
                hideStepIf=util.hideStepIfSuccess
            ))

            self.preliminary_steps.append(steps.DockerPull(
                label=basename,
                image=image,
                doStepIf=should_build,
                hideStepIf=util.hideStepIfSuccessOrSkipped
            ))
        else:
            image = '%s:%06d' % (
                basename,
                self.properties['buildnumber'][0],
            )

        common_args = {
            'label': basename,
            'image': image,
            'dockerfile': dockerfile,
            'context_dir': full_context_dir,
            'build_args': {
                'BUILDBOT_VERSION': buildbot.version
            },
            'labels': {
                'eve.build.ts': '{0:.0f}'.format(time())
            }
        }

        self.preliminary_steps.append(steps.DockerBuild(
            flunkOnFailure=False,
            haltOnFailure=False,
            hideStepIf=util.hideStepIfSuccessOrSkipped,
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

        @defer.inlineCallbacks
        def is_prev_build_failed(step):
            prec_failed_image = step.getProperty('DockerBuildFailed', '')
            current_image = yield step.build.render(step.image)
            defer.returnValue(prec_failed_image == current_image)

        self.preliminary_steps.append(steps.DockerBuild(
            name='[{0}] build retry'.format(basename)[0:49],
            is_retry=True,
            hideStepIf=util.hideStepIfSkipped,
            doStepIf=is_prev_build_failed,
            **common_args
        ))
        # end of workaround

        if use_registry:
            self.preliminary_steps.append(steps.DockerPush(
                label=basename,
                image=image,
                doStepIf=should_build,
                hideStepIf=util.hideStepIfSuccessOrSkipped
            ))

        return image
