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
"""Code coverage report publication buildbot step.

This file provide the `PublishCoverageReport` which is a buildbot step
class.
It's used to publish a generic code coverage report.

Content:
    - `PublicationBase`: Base class for all publication classes.
    - `CodecovIOPublication`: Codecov IO publication class.
    - `PublishCoverageReport`: Buildbot step to publish a code coverate report.

"""

import abc
import os
import shutil
import stat
import tempfile

import six
from buildbot.plugins import util
from buildbot.process import remotecommand, remotetransfer
from buildbot.process.buildstep import BuildStep
from buildbot.process.results import FAILURE, SKIPPED, SUCCESS, WARNINGS
from buildbot.util import httpclientservice
from twisted.internet import defer
from twisted.python import log

try:
    from urllib.parse import urlparse
except ImportError:
    import urlparse


@six.add_metaclass(abc.ABCMeta)
class PublicationBase(object):
    """Base class for all publication classes."""

    url_name = None
    """Name of the URL given to buildbot."""

    def __init__(self, repository, revision,
                 branch=None, name=None, flags=None, config_file=None):
        """`PublicationBase` constructor.

        Args:
            repository: Repository identifier (name or slug).
            revision: Version control revision ID (E.g. git changeset).
            branch: Branch name.
            name: Name of the code coverage report.
            flags: Code coverage report tags.
            config_file: Relative path of the configuration file (codecov.yml).

        """
        self.repository = repository
        self.revision = revision
        self.branch = branch
        self.name = name
        self.flags = flags
        self.config_file = config_file

        self.url = None

    @abc.abstractmethod
    def publish(self, master, reports):
        raise NotImplementedError()


class CodecovIOPublication(PublicationBase):
    """Code coverage publication class for codecov.io service."""

    url_name = 'codecov.io'
    """Name of the URL given to buildbot."""

    @defer.inlineCallbacks
    def publish(self, build, reports):
        """Publish all given code coverage report files.

        To publish a code coverage report to *codecov* service, we first need
        to make a request to notify codecov we want upload a new code coverage
        report.
        After that, ``codecov`` return us a temporary URL to S3 server where we
        can upload the code coverage report.

        For more details, see `codecov documentation`_.

        Args:
            build: Buildbot build which execute the PublishCoverageReport step.
            reports: List of code coverage report files to publish.

        Returns:
            (result, name, text).

            - *result*: Publish step result (*SUCCESS*, *FAILURE* or
                        *SKIPPED*).
            - *name* and *text* are respectively the title and the content of
              the buildbot complete log of the step.
              It's used to return additionnal information for the occured error
              or to give the skip reason.

        .. _codecov documentation:
           https://docs.codecov.io/v4.3.0/reference#upload

        """
        if not self.revision:
            defer.returnValue((FAILURE, 'error', 'Missing revision'))

        if not util.env.CODECOV_IO_UPLOAD_TOKEN:
            defer.returnValue((SKIPPED, 'reason',
                               'Codecov.io upload token not given to Eve'))

        (result, arg1, arg2) = yield self._send_to_codecov(build)
        if result != SUCCESS:
            defer.returnValue((result, arg1, arg2))
        else:
            (self.url, s3_url) = (arg1, arg2)

        result = yield self._send_to_s3(build, s3_url, reports)

        defer.returnValue(result)

    @defer.inlineCallbacks
    def _send_to_codecov(self, build):
        """Notify ``codecov`` we want upload a new code coverage report file.

        ``codecov`` need multiple query parameters:
            - *commit*: The destination commit sha for the report (mandatory)
            - *token*: A UUID token used to identify the project (mandatory).

            - *branch*: The target branch for the report. This value may
                        be overridden during the Codecov discovery process.
            - *build*: The build number provided by your CI service.
            - *job*: The job number provided by your CI service.
            - *build_url*: The http url to link back to your CI provider.
            - *name*: A custom name for this specific upload.
            - *slug*: The owner/repo slug name of the project.
            - *yaml*: The relative path to the codecov.yml in this project.
            - *service*: The CI service name (buildbot in our case).
            - *flags*: Used for Flags. Can be one or more flags. E.g.,
                       flags=unit or flags=unit,java
            - *pr*: The pull request number this commit is currently found in.

        Args:
            build: Buildbot build which execute the `PublishCoverageReport`
                step.

        """
        http = yield httpclientservice.HTTPClientService.getService(
            build.master, util.env.CODECOV_IO_BASE_URL, headers={
                'Accept': 'text/plain'
            }
        )

        build_url = yield build.getUrl()
        params = {
            'commit': self.revision,
            'token': util.env.CODECOV_IO_UPLOAD_TOKEN,
            'build': build.number,
            'build_url': build_url,
            'service': 'buildbot',
        }

        if self.config_file:
            params['yaml'] = self.config_file

        if self.branch:
            params['branch'] = self.branch

        if self.name:
            params['name'] = self.name

        if self.repository:
            params['slug'] = self.repository

        if self.flags:
            if isinstance(self.flags, list):
                flags = ','.join(self.flags)
            else:
                flags = self.flags
            params['flags'] = flags

        log.msg("Sending code coverage report to codecov.io"
                " for revision '{0}'...".format(self.revision))

        (result, content) = yield self.__send_request(
            http.post, '/upload/v4', params=params
        )

        if result == FAILURE:
            error = 'Unable to send request to "{0}": {1}'.format(
                util.env.CODECOV_IO_BASE_URL, content
            )
            defer.returnValue((FAILURE, 'error', error))

        lines = content.splitlines()
        if len(lines) != 2:
            error = 'Invalid response from codecov.io'
            log.msg("Error: {0}: {1}".format(error, content))
            defer.returnValue((FAILURE, 'error', error))

        (codecov_url, s3_url) = lines

        log.msg("Codecov URL: {0}".format(codecov_url))
        log.msg("S3 URL: {0}".format(s3_url))

        defer.returnValue((SUCCESS, codecov_url, s3_url))

    @defer.inlineCallbacks
    def _send_to_s3(self, build, s3_url, reports):
        """Store the code coverage report file in S3.

        Args:
            build: Buildbot build which execute the `PublishCoverageReport`
                step.
            s3_url (str): URL returned by ``codecov`` where we can upload
                the report.
            reports: List of code coverage report files.

        """
        s3_url_parts = urlparse.urlparse(s3_url)
        s3_url_endpoint = '{0}://{1}'.format(
            s3_url_parts.scheme, s3_url_parts.netloc
        )

        http = yield httpclientservice.HTTPClientService.getService(
            build.master, s3_url_endpoint,
            headers={
                'Content-Type': 'text/plain',
                'x-amz-acl': 'public-read',
                'x-amz-storage-class': 'REDUCED_REDUNDANCY'
            }
        )

        if len(reports) > 1:
            ok_result = (WARNINGS, 'reason',
                         'Multiple report files is not supported yet')
        else:
            ok_result = (SUCCESS, None, None)

        report = reports[0]

        try:
            with open(report, 'rb') as report_file:
                data = report_file.read()
        except (IOError, OSError) as exc:
            error = 'Unable to read "{0}": {1}'.format(
                report, exc.strerror or exc
            )
            defer.returnValue((FAILURE, 'error', error))

        # Convert query string params into dict
        params = dict(urlparse.parse_qsl(s3_url_parts.query))

        (result, reason) = yield self.__send_request(
            http.put, s3_url_parts.path, data=data, params=params
        )

        if result == FAILURE:
            error = 'Unable to send the code coverage file to ' \
                    '"{0}": {1}'.format(s3_url_endpoint, reason)
            defer.returnValue((FAILURE, 'error', error))
        else:
            defer.returnValue(ok_result)

    @staticmethod
    @defer.inlineCallbacks
    def __send_request(func, *args, **kwargs):
        try:
            response = yield func(*args, **kwargs)
        except Exception as exc:  # pylint: disable=broad-except
            reason = str(exc)
            defer.returnValue((FAILURE, reason))

        content = yield response.content()

        if response.code != 200:
            if content:
                reason = content
            else:
                reason = 'HTTP {0}'.format(response.code)
            defer.returnValue((FAILURE, reason))

        defer.returnValue((SUCCESS, content))


class _UploadCoverageReportsMixin(object):
    """Mixin class to upload code coverage report files from worker to master.

    We could have used `~buildbot.steps.transfer.MultipleFileUpload`.
    to do the job but:
        - This class allow to upload directory, what we don't want.
        - This class call directly the ``finished`` function after all upload.
          It's very difficult and dirty to override this behaviour.
        - This class can't ignore missing files.

    """

    maxSize = None
    """Maximum size, in bytes, of the file to write. The operation
    will fail if the file exceeds this size."""

    blockSize = 16 * 1024
    """The block size with which to transfer the file."""

    skipMissingFile = False
    """Skip or not missing files."""

    def __init__(self, **kwargs):
        super(_UploadCoverageReportsMixin, self).__init__(**kwargs)

        if not isinstance(self.filepaths, list):
            self.filepaths = [self.filepaths]

    def prepare_publication(self):
        """Prepare the upload of all code coverage report files.

        - Check availability of worker features.
        - Skip the upload if no given report files.

        """
        if not self.filepaths:
            self.addCompleteLog('reason', 'No given report')
            return SKIPPED

        self.checkWorkerHasCommand('stat')
        self.checkWorkerHasCommand('uploadFile')

        return super(_UploadCoverageReportsMixin, self).prepare_publication()

    @defer.inlineCallbacks
    def _statOnRemoteReport(self, filepath):
        """Execute 'stat' command on remote file.

        Returns:
            The output of `stat` or None if the given file doesn't exists on
            the worker.

        """
        args = {
            'file': filepath,
            'workdir': self.workdir,
        }
        cmd = remotecommand.RemoteCommand('stat', args)

        self.cmd = cmd
        try:
            yield self.runCommand(cmd)
        finally:
            self.cmd = None

        if not cmd.didFail():
            result = cmd.updates['stat'][-1]
        else:
            result = None

        defer.returnValue(result)

    @defer.inlineCallbacks
    def _uploadRemoteReport(self, workersrc, masterdest):
        """Upload the remote file into the master.

        Args:
            workersrc (str): Path of the file to upload in the worker.
            masterdest (str): Path of the file to write in the master.

        """
        file_writer = remotetransfer.FileWriter(masterdest, self.maxSize, None)

        args = {
            'workdir': self.workdir,
            'writer': file_writer,
            'maxsize': self.maxSize,
            'blocksize': self.blockSize,
            'keepstamp': False,
            'workersrc': workersrc,
        }
        cmd = remotecommand.RemoteCommand('uploadFile', args)

        self.cmd = cmd
        try:
            yield self.runCommand(cmd)
        except Exception:
            file_writer.cancel()
            raise
        finally:
            self.cmd = None

        if cmd.didFail():
            file_writer.cancel()
            defer.returnValue(FAILURE)

        defer.returnValue(SUCCESS)

    @defer.inlineCallbacks
    def uploadCoverageReports(self, destdir):
        """Upload all code coverage report files from worker.

        Args:
            destdir (str): Path of the dir on the master to store reports.

        """
        workersrcs = []
        for workersrc in set(self.filepaths):
            st_file = yield self._statOnRemoteReport(workersrc)
            if not st_file:
                if self.skipMissingFile:
                    continue

                self.addCompleteLog('error', 'File "{0}" not found'.format(
                    workersrc
                ))
                defer.returnValue((FAILURE, None))

            if not stat.S_ISREG(st_file[stat.ST_MODE]):
                self.addCompleteLog(
                    'error', 'File "{0}" is not a regular file'.format(
                        workersrc
                    )
                )
                defer.returnValue((FAILURE, None))

            workersrcs.append(workersrc)

        if not workersrcs:
            self.addCompleteLog('reason', 'No report found')
            defer.returnValue((SKIPPED, None))

        reports = []
        for workersrc in workersrcs:
            masterdest = os.path.join(destdir, os.path.basename(workersrc))
            result = yield self._uploadRemoteReport(workersrc, masterdest)
            if result == FAILURE:
                defer.returnValue(result)

            reports.append(masterdest)

        defer.returnValue((SUCCESS, reports))


class PublishCoverageReport(_UploadCoverageReportsMixin, BuildStep):
    """Publish a code coverage report to an external service."""

    publication_cls = CodecovIOPublication
    """Publication class to use."""

    name = 'publish code coverage report'
    """Name of the buildbot step."""

    parms = BuildStep.parms + [
        'repository',
        'revision',
        'filepaths',
        'branch',
        'uploadName',
        'flags',
        'configFile',
        'skipMissingFile',
        'maxSize',
        'blockSize',
    ]

    renderables = [
        'repository',
        'revision',
        'filepaths',
        'branch',
        'uploadName',
        'flags',
        'configFile',
    ]

    repository = None
    """Repository identifier (name or slug)."""

    revision = None
    """Version control revision ID (E.g. git changeset)."""

    filepaths = None
    """List of code coverage report files to publish."""

    branch = None
    """Branch name."""

    uploadName = None
    """Name of the code coverage report."""

    flags = None
    """Code coverage report tags."""

    configFile = None
    """Relative path of the configuration file (codecov.yml)."""

    def __init__(self, **kwargs):
        super(PublishCoverageReport, self).__init__(**kwargs)

        self.tmpdir = None

    def prepare_publication(self):
        """Prepare the upload of all code coverage report files.

        Create a temporary directory in the master to store all reports from
        the buildbot worker.

        """
        try:
            self.tmpdir = tempfile.mkdtemp(
                prefix='eve_publish_coverage_report_'
            )
        except (OSError, IOError) as exc:
            self.addCompleteLog(
                'error', 'Unable to create a temporary directory '
                         'to retrieve coverage report files '
                         'from worker: {0}'.format(
                             exc.strerror or exc
                         )
            )
            return FAILURE
        else:
            return SUCCESS

    @defer.inlineCallbacks
    def startUploadAndPublishReports(self, tmpdir):
        publication = self.publication_cls(
            self.repository, self.revision,
            branch=self.branch,
            name=self.uploadName,
            flags=self.flags,
            config_file=self.configFile,
        )

        (result, reports) = yield self.uploadCoverageReports(tmpdir)
        if result in [SUCCESS, WARNINGS]:
            (result, name, text) = yield publication.publish(
                self.build, reports
            )

            if result == SUCCESS and \
               publication.url_name and \
               publication.url:
                self.addURL(
                    publication.url_name,
                    publication.url
                )

            if name and text:
                self.addCompleteLog(name, text)

        defer.returnValue(result)

    @defer.inlineCallbacks
    def run(self):
        """Start the publish step.

        Mandatory arguments:
            - **repository**: Name of the git repository.
            - **revision**:  The destination commit sha for the report.
            - **filepaths**: List of code coverage report file path.

        Optional arguments:
            - **branch**: Name of the branch.
            - **uploadName**: Upload identifier.
            - **flags**: List of report flag.
            - **skipMissingFile**: Skip or not missing report file.
            - **maxSize**: Upload max size.
            - **blockSize**: Upload block size.

        """
        result = self.prepare_publication()
        if result != SUCCESS:
            defer.returnValue(result)

        nsrcs = len(self.filepaths)
        self.descriptionDone = 'publishing {0:d} coverage {1}'.format(
            nsrcs, 'report' if nsrcs == 1 else 'reports'
        )

        try:
            results = yield self.startUploadAndPublishReports(self.tmpdir)
        except Exception:  # pylint: disable=broad-except
            results = FAILURE

        log.msg('Removing temporary directory "{0}"...'.format(self.tmpdir))

        def warnOnError(_func, path, excinfo):
            log.msg('Warning: Unable to remove "{0}": {1}'.format(
                path, excinfo
            ))

        shutil.rmtree(self.tmpdir, onerror=warnOnError)

        defer.returnValue(results)
