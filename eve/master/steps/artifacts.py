"""Steps allowing eve to interact with artifacts."""

import json
import re
from collections import defaultdict
from os import path

from buildbot.process import logobserver
from buildbot.process.properties import Interpolate
from buildbot.process.results import FAILURE, SKIPPED
from buildbot.steps.shell import SetPropertyFromCommand, ShellCommand
from twisted.internet import defer, reactor

CURL_CMD = """curl -s -X POST -H "Content-type: application/json" \
--progress-bar https://identity.api.rackspacecloud.com/v2.0/tokens \
-d '{ \
        "auth": { \
            "passwordCredentials": { \
                "username": "'$RAX_LOGIN'", \
                "password": "'$RAX_PWD'" \
            } \
        } \
    }'
"""


class CloudfilesAuthenticate(SetPropertyFromCommand):
    """Authenticate with rackspace and store the auth token on a property."""

    def __init__(self, rax_login, rax_pwd, **kwargs):
        SetPropertyFromCommand.__init__(
            self,
            name='get cloudfiles authentication params',
            command=CURL_CMD,
            property='cloudfiles_token',
            haltOnFailure=True,
            env={'RAX_LOGIN': rax_login, 'RAX_PWD': rax_pwd},
            logEnviron=False,  # Obfuscate $RAX_PWD
            **kwargs
        )

    def commandComplete(self, cmd):  # NOQA flake8 to ignore camelCase
        if cmd.didFail():
            return
        output = json.loads(self.observer.getStdout())
        token = output["access"]["token"]["id"]
        self.setProperty(self.property, str(token), "CloudfilesAuthenticate")
        self.property_changes[self.property] = token


class Upload(ShellCommand):
    """Upload files to rackspace."""

    # maximum upload time, in seconds.
    UPLOAD_MAX_TIME = 900

    def __init__(self, source, urls=None, **kwargs):
        name = kwargs.pop('name', 'send artifacts to artifact repository')
        self._retry = kwargs.pop('retry', (0, 1))
        self._source = source
        self._kwargs = kwargs
        self._urls = urls

        command = [
            'cd ' + source,
            ('[ "$(ls -A)" ]'
             ' || (echo "Directory is empty. Nothing to do."; exit 1)'),
            'tar -chvzf ../artifacts.tar.gz . ',
            'echo tar successful. Calling curl... ',
            ('curl --verbose --max-time {max_time} -s -T ../artifacts.tar.gz '
             '-X PUT -H"x-auth-token: %(prop:cloudfiles_token)s" ' +
             self.CLOUDFILES_URL + self.ARTIFACTS_PREFIX +
             '%(prop:build_id)s' +
             '?extract-archive=tar.gz').format(max_time=self.UPLOAD_MAX_TIME)
        ]

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

        ShellCommand.__init__(
            self,
            name=name,
            haltOnFailure=True,
            command=Interpolate(' && '.join(command)),
            maxTime=self.UPLOAD_MAX_TIME + 10,
            **kwargs
        )
        self.observer = logobserver.BufferLogObserver(wantStdout=True,
                                                      wantStderr=True)
        self.addLogObserver('stdio', self.observer)

    @defer.inlineCallbacks
    def run(self):
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
                    source=self._source,
                    urls=self._urls,
                    retry=(delay, repeats - 1),
                    **self._kwargs)])
                defer.returnValue(SKIPPED)
        defer.returnValue(result)

    def evaluateCommand(self, cmd):  # NOQA flake8 to ignore camelCase
        out = self.observer.getStdout()
        err = self.observer.getStderr()
        if ('Cowardly refusing to create an empty archive' in err
                or 'No such file or directory' in err
                or 'File removed before we read it' in err
                or 'Directory is empty' in out):
            return SKIPPED
        elif 'Response Status: 201 Created' not in out:
            return FAILURE
        return cmd.results()

    # regexp use to make the difference between simple link prefix and link
    # name patterns
    PREFIX_PATTERN_ELEMENTS = re.compile(r'\\\d+')

    def commandComplete(self, cmd):  # NOQA flake8 to ignore camelCase
        # if command failed or was skipped, no need to publish urls
        if self.evaluateCommand(cmd) in [SKIPPED, FAILURE]:
            return

        # extracts file path used in urls, in command output:
        lines = self.observer.getStdout().split('\n')
        links = set()
        for link in self._links:
            matches = []
            start = lines.index(link['header'])
            for line in lines[start + 1:]:
                if line == '':
                    break
                matches.append(line)

            if not matches:
                continue
            if (len(matches) == 1
                    and '*' not in link['path'] and '?' not in link['path']
                    and 'name' in link):
                links.add((link['name'], matches[0]))
            else:
                prefix = link['name'] if 'name' in link else ''

                # case 1 : prefix is a pattern
                if self.PREFIX_PATTERN_ELEMENTS.search(prefix):
                    path_pattern = re.compile(
                        '^./' +
                        link['path'].replace('*', '(.*)').replace('?', '(.)') +
                        '$')
                    links.update([
                        (path_pattern.sub(prefix, match), match)
                        for match in matches
                    ])

                # case 2 : prefix does not contain pattern
                else:
                    links.update([
                        ('{prefix}{name}'.format(
                            prefix=prefix, name=match.split('/')[-1]),
                         match)
                        for match in matches
                    ])

        links = sorted(links)

        # append path to names if several links share the same name
        pathes = defaultdict(int)
        for name, _ in links:
            pathes[name] += 1
        for index, (name, upath) in enumerate(links):
            if pathes[name] > 1:
                links[index] = (
                    '{name} ({detail})'.format(name=name, detail=upath[2:]),
                    upath)

        # adds links in step display, based on existing files
        for (name, upath) in links:
            url = ('{url}/{prefix}{build_id}/{path}'.format(
                url=self.ARTIFACTS_URL,
                prefix=self.ARTIFACTS_PREFIX,
                build_id=self.getProperty('build_id'),
                path=upath
            ))
            self.addURL(name, url)


class Download(ShellCommand):
    """Download files from rackspace."""

    def __init__(self, files, **kwargs):
        name = kwargs.pop(
            'name', 'downloads artifacts from artifact repository')
        self._retry = kwargs.pop('retry', (0, 1))
        self._kwargs = kwargs

        command = []
        for fpath in files:
            url = '{url}/{prefix}%(prop:build_id)s'.format(
                url=self.ARTIFACTS_URL,
                prefix=self.ARTIFACTS_PREFIX)

            # inserts artifacts login / pwd in url
            url = url.replace(
                'https://',
                'https://{login}:{password}@'.format(
                    login=self.ARTIFACTS_LOGIN,
                    password=self.ARTIFACTS_PWD
                ))

            output = fpath

            command.append(
                'echo "> download {path} from artifacts into {output}"'.format(
                    path=fpath,
                    output=output
                ))

            output_dir = path.dirname(fpath)
            if output_dir:
                command.append(
                    'mkdir -p {output_dir}'.format(output_dir=output_dir))

            command.append(
                'curl --silent --retry 10 -s --fail '
                '--output {output} '
                '{url}/{path}'.format(url=url, path=fpath, output=output))

        ShellCommand.__init__(
            self,
            name=name,
            haltOnFailure=True,
            command=Interpolate(' && '.join(command)),
            **kwargs
        )
        self.observer = logobserver.BufferLogObserver(wantStdout=True,
                                                      wantStderr=True)
        self.addLogObserver('stdio', self.observer)
