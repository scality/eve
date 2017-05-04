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

"""All docker build related steps."""

from buildbot.locks import MasterLock
from buildbot.process.results import FAILURE
from buildbot.steps.master import MasterShellCommand
from twisted.internet import defer

DOCKER_BUILD_LOCK = MasterLock('docker_build')


class DockerBuild(MasterShellCommand):
    """Step to build a docker image on eve docker host."""

    def __init__(self, image, dockerfile=None, is_retry=False,
                 labels=None, build_args=None, **kwargs):
        self.image = image
        self.is_retry = is_retry
        kwargs.setdefault('locks', []).append(
            DOCKER_BUILD_LOCK.access('exclusive')
        )

        command = [
            'docker', 'build',
            '--tag', image
        ]

        if labels:
            for label_name, label_value in labels.iteritems():
                command += ['--label', '{0}={1}'.format(
                    label_name, label_value
                )]

        if build_args:
            for build_arg_name, build_arg_value in build_args.iteritems():
                command += [
                    '--build-arg', '{0}={1}'.format(
                        build_arg_name,
                        build_arg_value
                    )
                ]

        if dockerfile is not None:
            command += ['--file', dockerfile]

        if is_retry:
            command += ['--no-cache']

        command += ['.']

        super(DockerBuild, self).__init__(command, **kwargs)

    def isNewStyle(self):  # flake8: noqa
        # needed because we redefine `run` below
        return False

    @defer.inlineCallbacks
    def run(self):
        result = yield super(DockerBuild, self).run()
        if result == FAILURE:
            properties = self.build.getProperties()
            properties.setProperty(
                'DockerBuildFailed', self.image, self.name, runtime=True)
        defer.returnValue(result)

    def __hash__(self):
        return hash(self.image)

    def __eq__(self, other):
        return (isinstance(other, DockerBuild) and
                self.image == other.image and
                (self.is_retry) == (other.is_retry))
