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

"""Steps snooping on test results in JUnit format."""
import os
from StringIO import StringIO
from xml.etree.ElementTree import ParseError

from buildbot.process.buildstep import CommandMixin
from buildbot.process.results import FAILURE, WARNINGS
from buildbot.steps.shell import ShellCommand
from buildbot.steps.worker import CompositeStepMixin
from twisted.internet import defer
from xunitparser import Parser, to_timedelta  # pylint: disable=import-error


class CustomJUnitParser(Parser):
    """Customize original xunitparser, too strict for our reports."""

    def parse_root(self, root):
        """Customize original parse_root."""
        tsuite = self.TS_CLASS()
        if root.tag == 'testsuites':
            for subroot in root:
                self.parse_testsuite(subroot, tsuite)
        else:
            self.parse_testsuite(root, tsuite)

        tresults = tsuite.run(self.TR_CLASS())

        tresults.time = to_timedelta(root.attrib.get('time'))
        return (tsuite, tresults)


class JUnitShellCommand(ShellCommand, CommandMixin, CompositeStepMixin):
    """A ShellCommand that sniffs junit output."""

    failures = 0
    errors = 0
    skipped = 0
    total = 0
    first_failure = None
    first_error = None
    name = 'junit_shell'
    renderables = ['report_dir']

    def __init__(self, report_dir=None, *args, **kwargs):
        super(JUnitShellCommand, self).__init__(*args, **kwargs)
        self.report_dir = report_dir

    def fail_or_warning(self, cmd):
        """Return failure if the command failed, warning otherwise."""
        if cmd.didFail():
            self.finished(FAILURE)
        self.finished(WARNINGS)

    @defer.inlineCallbacks
    def commandComplete(self, cmd):  # flake8: noqa
        if not self.report_dir:
            self.fail_or_warning(cmd)
            return

        has_path = yield self.pathExists(
            self.build.path_module.join(self.workdir, self.report_dir))

        if not has_path:
            self.fail_or_warning(cmd)
            return

        contents = yield self.runGlob(
            os.path.join(self.workdir, self.report_dir, '*.xml'))

        if not contents:
            self.fail_or_warning(cmd)
            return

        for report_file in contents:
            yield self.parse_report(report_file)

        if self.failures or self.errors:
            self.finished(FAILURE)
            return

        if not self.total:
            self.fail_or_warning(cmd)
            return

    @defer.inlineCallbacks
    def parse_report(self, report_file):
        """Retrieve report from remote worker, parse it, and update stats."""
        report = yield self.getFileContentFromWorker(
            report_file, abandonOnFailure=True)

        memfile = StringIO(report)

        try:
            _, tresults = CustomJUnitParser().parse(memfile)
        except (ParseError, AssertionError):
            # ignore non-xunit content
            return

        self.failures += len(tresults.failures)
        self.errors += len(tresults.errors)
        self.skipped += len(tresults.skipped)
        self.total += tresults.testsRun

        if not self.first_failure and tresults.failures:
            self.first_failure = tresults.failures[0][0].id()
        if not self.first_error and tresults.errors:
            self.first_error = tresults.errors[0][0].id()

    def getResultSummary(self):  # flake8: noqa
        if not self.total:
            return {u'step': u'no test results found'}

        if self.first_error:
            return {u'step': u'ERROR: %s' % self.first_error}

        if self.first_failure:
            return {u'step': u'FAIL: %s' % self.first_failure}

        return {u'step': u'T:%d E:%d F:%d S:%d' % (
            self.total,
            self.errors,
            self.failures,
            self.skipped
        )}
