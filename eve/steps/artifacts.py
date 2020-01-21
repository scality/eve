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
"""Steps allowing eve to interact with artifacts."""

import abc
import os
import re
from collections import defaultdict

from buildbot.plugins import util
from buildbot.process import logobserver
from buildbot.process.properties import Interpolate
from buildbot.process.results import FAILURE, SKIPPED, SUCCESS
from buildbot.steps.shell import ShellCommand
from packaging import version
from twisted.internet import defer, reactor

from .property import EvePropertyFromCommand


def get_artifacts_base_name():
    """Give containing the base name of artifacts container."""
    return (
        '%(prop:git_host)s:%(prop:git_owner)s:%(prop:git_slug)s:'
        + util.env.ARTIFACTS_PREFIX
        + '%(prop:product_version)s.r%(prop:commit_timestamp)s'
        + '.%(prop:commit_short_revision)s'
    )


def get_artifacts_name(buildnumber, stage_name):
    """Give interpolate containing the full name of artifacts container."""
    b4nb = buildnumber.zfill(8)
    return Interpolate(
        get_artifacts_base_name()
        + '.' + stage_name + '.' + b4nb
    )


class MalformedArtifactsNameProperty(Exception):
    pass


class GetArtifactsFromStage(EvePropertyFromCommand):
    """Get artifacts from another stage and store it in a property."""

    def __init__(self, stage, **kwargs):
        assert 'command' not in kwargs
        name = kwargs.pop(
            'name', 'get artifacts name from stage: %s' % str(stage))
        super(GetArtifactsFromStage, self).__init__(
            name=name,
            command=[
                'curl',
                '-L',
                '--fail',
                '-I',
                Interpolate('http://artifacts/last_success/{}.{}'.format(
                            get_artifacts_base_name(),
                            stage)),
            ],
            **kwargs
        )

    def commandComplete(self, cmd):  # NOQA flake8 to ignore camelCase
        if cmd.didFail():
            return

        # parse the response headers to get the container from redirection
        artifacts_name = 'fatal: unable to parse artifacts name'
        lines = self.observer.getStdout().splitlines()
        for line in lines:
            reg = re.search('^Location: (https?://.*?)/builds/(.*)$', line)
            if reg:
                artifacts_name = reg.group(2)
                break

        self.setProperty(self.property, str(artifacts_name),
                         'GetArtifactsFromStage')
        self.property_changes[self.property] = artifacts_name


class SetArtifactsName(EvePropertyFromCommand):
    def __init__(self, buildnumber, stage_name):
        super(SetArtifactsName, self).__init__(
            name='set the artifacts name',
            command=[
                'echo',
                get_artifacts_name(buildnumber, stage_name)
            ],
            hideStepIf=util.hideStepIfSuccess,
            property='artifacts_name',
            logEnviron=False)


class SetArtifactsPublicURL(EvePropertyFromCommand):
    def __init__(self):
        super(SetArtifactsPublicURL, self).__init__(
            name='set the artifacts public url',
            command=[
                'echo',
                Interpolate(util.env.ARTIFACTS_PUBLIC_URL
                            + '/builds/%(prop:artifacts_name)s'),
            ],
            hideStepIf=util.hideStepIfSuccess,
            property='artifacts_public_url',
            logEnviron=False)


class SetArtifactsPrivateURL(EvePropertyFromCommand):
    def __init__(self, is_vm):
        super(SetArtifactsPrivateURL, self).__init__(
            name='set the artifacts private url',
            command=[
                'echo',
                Interpolate(
                    'http://artifacts/builds/%(prop:artifacts_name)s'),
            ],
            hideStepIf=util.hideStepIfSuccess,
            property='artifacts_private_url',
            logEnviron=False)


class BaseUpload(ShellCommand):
    """Base class to handle artifacts uploads."""

    __metaclass__ = abc.ABCMeta

    renderables = [
        'source',
    ]
    _links = []

    DEFAULT_UPLOAD_MAX_TIME = 3600
    """Maximum upload time, in seconds."""

    def __init__(self, source, urls=None, **kwargs):
        name = kwargs.pop('name', 'send artifacts to artifact repository')
        self._retry = kwargs.pop('retry', (0, 1))
        self.source = source
        self._kwargs = kwargs
        self._urls = urls
        self._upload_max_time = kwargs.get(
            'maxTime', self.DEFAULT_UPLOAD_MAX_TIME)

        kwargs['workdir'] = kwargs.get('workdir',
                                       util.Transform(os.path.join,
                                                      'build',
                                                      source))
        super(BaseUpload, self).__init__(
            name=name,
            haltOnFailure=True,
            command=util.Transform(self.set_command, urls),
            maxTime=self._upload_max_time + 10,
            **kwargs
        )
        self.observer = logobserver.BufferLogObserver(wantStdout=True,
                                                      wantStderr=True)
        self.addLogObserver('stdio', self.observer)

    @property
    @abc.abstractmethod
    def upload_command(self):
        """Return a string with the command to make an upload to Artifacts."""
        return

    def get_container(self):
        eve_api_version = self.getProperty('eve_api_version')
        if version.parse(eve_api_version) >= version.parse('0.2'):
            return self.getProperty('artifacts_name')
        else:
            return util.env.ARTIFACTS_PREFIX + self.getProperty('build_id')

    def set_command(self, urls):
        command = self.upload_command

        # compute configured urls
        links = []
        if urls:
            for upath in urls:
                if isinstance(upath, tuple) or isinstance(upath, list):
                    link = {'name': upath[0], 'path': upath[1]}
                else:
                    link = {'path': upath}
                link['header'] = 'find files matching {path}:'.format(
                    path=link['path'])
                links.append(link)

        for link in links:
            command.append(
                'echo -e "\\n{header}\\n'
                '$(find -L . -type f -path \'./{path}\')'
                '\\n\\n"'.format(
                    header=link['header'],
                    path=link['path']
                ))
        self._links = links

        return ' && '.join(command)

    def check_artifacts_name(self):
        """Check that artifacts name has not been overwritten."""
        eve_api_version = self.getProperty('eve_api_version')
        if version.parse(eve_api_version) >= version.parse('0.2'):
            artifacts_name_property = self.getProperty('artifacts_name')
            regexp_staging = re.compile(
                r'^((.*):)?%s[0-9]+(\.[0-9]+){1,3}\.r([0-9]{12})\.'
                r'([0-9a-f]+)(\.(.*)\.([0-9]+))?$' % util.env.ARTIFACTS_PREFIX)
            if not regexp_staging.match(artifacts_name_property):
                raise MalformedArtifactsNameProperty

    # regexp use to make the difference between simple link prefix and link
    # name patterns
    PREFIX_PATTERN_ELEMENTS = re.compile(r'\\\d+')

    def commandComplete(self, cmd):  # NOQA flake8 to ignore camelCase
        # if command failed or was skipped, no need to publish urls
        if self.evaluateCommand(cmd) in [SKIPPED, FAILURE]:
            return

        # extracts file path used in urls, in command output:
        links = self._get_links_from_stdout()

        # append path to names if several links share the same name
        paths = defaultdict(int)
        for name, _ in links:
            paths[name] += 1
        for index, (name, upath) in enumerate(links):
            if paths[name] > 1:
                links[index] = (
                    '{name} ({detail})'.format(name=name, detail=upath[2:]),
                    upath)

        # adds links in step display, based on existing files
        for (name, upath) in links:
            url = ('{url}/builds/{container}/{path}'.format(
                url=util.env.ARTIFACTS_PUBLIC_URL,
                container=self.get_container(),
                path=upath
            ))
            self.addURL(name, url)

    def _get_links_from_stdout(self):
        lines = self.observer.getStdout().split('\n')
        links = set()
        for link in self._links:
            matches = []
            try:
                start = lines.index(link['header'])
            except ValueError:
                # lines may be empty or not have the header
                # (missing an expected artefact)
                continue
            for line in lines[start + 1:]:
                if line == '':
                    break
                matches.append(line)

            if not matches:
                continue
            if (len(matches) == 1
                    and '*' not in link['path']
                    and '?' not in link['path']
                    and 'name' in link):
                links.add((link['name'], matches[0]))
            else:
                prefix = link['name'] if 'name' in link else ''

                # case 1 : prefix is a pattern
                if self.PREFIX_PATTERN_ELEMENTS.search(prefix):
                    path_pattern = re.compile(
                        '^./'
                        + link['path'].replace('*', '(.*)').replace('?', '(.)')
                        + '$')
                    links.update([
                        (path_pattern.sub(prefix, match), match)
                        for match in matches
                    ])

                # case 2 : prefix does not contain pattern
                else:
                    links.update([
                        ('{prefix}{name}'.format(
                            prefix=prefix,
                            name=match.split('/')[-1]),
                         match)
                        for match in matches
                    ])

        return sorted(links)


class Upload(BaseUpload):
    """Upload files to artifacts."""

    @property
    def upload_command(self):
        return [
            ('if [ ! -n "$(find -L . -type f | head -1)" ]; then '
             'echo "No files here. Nothing to do."; exit 0; fi'),
            'tar -chvzf ../artifacts.tar.gz .',
            'echo tar successful. Calling curl...',
            ('curl --progress-bar --verbose --max-time {} -T '
             '../artifacts.tar.gz -X PUT http://artifacts/upload/{}').format(
                self._upload_max_time,
                self.get_container())]

    @defer.inlineCallbacks
    def run(self):
        self.check_artifacts_name()
        result = yield super(Upload, self).run()
        if result == FAILURE:
            delay, repeats = self._retry
            if repeats > 0:
                # Wait for delay before retrying
                sleep_df = defer.Deferred()
                reactor.callLater(delay, sleep_df.callback, None)
                yield sleep_df

                # Schedule a retry after this step
                self.build.addStepsAfterCurrentStep([self.__class__(
                    source=self.source,
                    urls=self._urls,
                    retry=(delay, repeats - 1),
                    **self._kwargs)])
                defer.returnValue(SKIPPED)
        if util.env.ARTIFACTS_VERSION_THREE_IN_USE:
            self.build.addStepsAfterCurrentStep([Uploadv3(
                source=self.source,
                urls=self._urls,
                flunkOnFailure=False,
                warnOnFailure=True,
                **self._kwargs
            )])
        defer.returnValue(result)

    def evaluateCommand(self, cmd):  # NOQA flake8 to ignore camelCase
        out = self.observer.getStdout()
        err = self.observer.getStderr()
        if not err and 'No files here. Nothing to do.' in out:
            return SUCCESS
        elif 'Response Status: 201 Created' not in out:
            return FAILURE
        return cmd.results()


class Uploadv3(BaseUpload):
    """Upload files to artifacts version >= 3.

    This class was created to cohexist Upload while we pla
    """

    @property
    def upload_command(self):
        return [
            ('find -L -type f -print0 | '
             'sed -e "s:\(^\|\x0\)\./:\1:g" | '
             'xargs -0 -n 1 -t -P 16 '
             '-I @ curl --silent --fail --show-error --max-time {} '
             '-T "@" "http://artifacts-v3/upload/{}/@"').format(
                self._upload_max_time, self.get_container())]

    @defer.inlineCallbacks
    def run(self):
        self.check_artifacts_name()
        result = yield super(Uploadv3, self).run()
        defer.returnValue(result)
