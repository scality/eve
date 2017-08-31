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
from buildbot.process import logobserver
from buildbot.process.results import FAILURE, SUCCESS
from buildbot.steps.master import MasterShellCommand
from twisted.internet import defer

DOCKER_BUILD_LOCK = MasterLock('docker_build')


class DockerBuild(MasterShellCommand):
    """Build a Docker image.

    Parameters:
        label (str): the reference name of the image (for display in UI).
        image (Interpolate): the full repo:name:tag of the image to build.

    Optional Parameters:
        dockerfile (str): use the specified Dockerfile.
        is_retry (bool): set to True if this step was already tried before.
        labels (dict): provide additionnal label definitions to the
            ``docker build`` command.
        build_args (dict): provide additional ``--build-args`` to the
            ``docker build`` command.

    """

    renderables = [
        'image',
    ]

    def __init__(self, label, image, dockerfile=None, is_retry=False,
                 labels=None, build_args=None, **kwargs):
        kwargs.setdefault('name',
                          '[{0}] build'.format(label)[0:49])
        self.image = image
        self.is_retry = is_retry
        kwargs.setdefault('locks', []).append(
            DOCKER_BUILD_LOCK.access('exclusive')
        )
        command = ['docker', 'build', '--tag', image]

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

        super(DockerBuild, self).__init__(command, logEnviron=False, **kwargs)

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


class DockerCheckLocalImage(MasterShellCommand):
    """Check for existence of a Docker image locally.

    Look up the fingerprint of given image in local images, and sets
    the ``exists_[label]`` property either to ``True`` or ``False``.

    Parameters:
        label (str): the reference name of the image
            (for display in UI and property).
        image (interpolate): the full repo:name:tag of the image to look up.

    See Also:
        :py:class:`DockerComputeImageFingerprint`.

    """

    def __init__(self, label, image, **kwargs):
        kwargs.setdefault('name', '[{0}] look up'.format(label)[:49])
        kwargs.setdefault('locks', []).append(
            DOCKER_BUILD_LOCK.access('exclusive')
        )
        self.label = label
        super(DockerCheckLocalImage, self).__init__(
            ['docker', 'image', 'inspect', image],
            logEnviron=False, **kwargs)

    def isNewStyle(self):  # flake8: noqa
        # needed because we redefine `run` below
        return False

    @defer.inlineCallbacks
    def run(self):
        result = yield super(DockerCheckLocalImage, self).run()
        properties = self.build.getProperties()
        properties.setProperty(
            'exists_{0}'.format(self.label),
            result == SUCCESS,
            'DockerCheckLocalImage',
            runtime=True)
        defer.returnValue(SUCCESS)


class DockerComputeImageFingerprint(MasterShellCommand):
    """Compute the fingerprint of a docker context.

    This step computes the sha256 fingerprint of an image given its context
    and stores it to the property ``fingerprint_[label]``.

    Parameters:
        label (str): the reference name of the image
            (for display in UI and property).
        context_dir (str): full path to the context directory.

    """

    def __init__(self, label, context_dir, **kwargs):
        kwargs.setdefault('name',
                          '[{0}] fingerprint'.format(label)[:49])
        self.label = label
        super(DockerComputeImageFingerprint, self).__init__(
            'tar -c --mtime="1990-02-11 00:00Z" --group=0 ' \
            '--owner=0 --numeric-owner --sort=name --mode=0 . ' \
            '| sha256sum | cut -f 1 -d " "',
            workdir=context_dir, logEnviron=False, **kwargs
        )
        self.observer = logobserver.BufferLogObserver(wantStdout=True,
                                                      wantStderr=True)
        self.addLogObserver('stdio', self.observer)

    def isNewStyle(self):  # flake8: noqa
        # needed because we redefine `run` below
        return False

    @defer.inlineCallbacks
    def run(self):
        result = yield super(DockerComputeImageFingerprint, self).run()
        fingerprint = self.observer.getStdout().splitlines()[0]
        properties = self.build.getProperties()
        properties.setProperty(
            'fingerprint_{0}'.format(self.label),
            fingerprint,
            'DockerComputeImageFingerprint',
            runtime=True)
        defer.returnValue(result)


class DockerPull(MasterShellCommand):
    """Pull an image from a registry.

    This step attempts to pull an image from a registry referenced in the
    provided image name itself, and stores the result (True or False) to
    the property ``exists_[label]``.

    Parameters:
        label (str): the reference name of the image
            (for display in UI and property).
        image (interpolate): the full repo:name:tag of the image to look up.

    """

    def __init__(self, label, image, **kwargs):
        kwargs.setdefault('name',
                          '[{0}] pull'.format(label)[:49])
        kwargs.setdefault('locks', []).append(
            DOCKER_BUILD_LOCK.access('exclusive')
        )
        self.label = label
        super(DockerPull, self).__init__(
            ['docker', 'pull', image],
            logEnviron=False, **kwargs)

    def isNewStyle(self):  # flake8: noqa
        # needed because we redefine `run` below
        return False

    @defer.inlineCallbacks
    def run(self):
        result = yield super(DockerPull, self).run()
        properties = self.build.getProperties()
        properties.setProperty(
            'exists_{0}'.format(self.label),
            result == SUCCESS,
            'DockerPull',
            runtime=True)
        defer.returnValue(SUCCESS)


class DockerPush(MasterShellCommand):
    """Push a Docker image to the custom registry.

    This step attempts to push an image to a registry referenced in the
    provided image name itself.

    Parameters:
        label (str): the reference name of the image (for display in UI).
        image (interpolate): the full repo:name:tag of the image to look up.

    """

    renderables = [
        'image',
    ]

    def __init__(self, label, image, **kwargs):
        kwargs.setdefault('name',
                          '[{0}] push'.format(label)[0:49])
        kwargs.setdefault('locks', []).append(
            DOCKER_BUILD_LOCK.access('exclusive')
        )
        self.image = image
        super(DockerPush, self).__init__(['docker', 'push', image],
                                         logEnviron=False, **kwargs)

    def __hash__(self):
        return hash(self.image)

    def __eq__(self, other):
        return (isinstance(other, DockerPush) and
                self.image == other.image)
