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

import os
import unittest

from tests.system.codecovio.codecov_io_server import CodecovIOMockServer
from tests.util.cluster import Cluster
from tests.util.yaml_factory import PreMerge


class TestPublishCodeCoverage(unittest.TestCase):
    """Test code coverage report publication step.

    ``PublishCodeCoverage`` is the generic buildbot step to use to
    publish several code coverage reports to an external service.
    At this moment, only ``codecov.io`` service is supported.

    These tests are two operating modes:
        - The first is to use an internal mock ``codecov.io`` server.
        - The second use the real ``codecov.io`` service.

    By default, in the automatic tests, we use the mock ``codecov.io``
    server to avoid being dependent external services that could not
    be available in the future.

    To use the real ``codecov.io`` server, we need to define the
    environment variable **CODECOV_IO_UPLOAD_TOKEN** which is the
    ``codecov.io`` upload token of the repository given in
    *yaml/generate_coverage_report/main.yml* YAML file.

    """

    def __init__(self, *args, **kwargs):
        super(TestPublishCodeCoverage, self).__init__(*args, **kwargs)

        self.codecov_io_server = None

    def setUp(self):
        """Instantiate a ``codecov.io`` mock HTTP server if needed.

        We define the **CODECOV_IO_BASE_URL** environment variable to
        communicate with our mock HTTP server rather than the real
        ``codecov.io`` server (see
        `~master/steps/publish_coverage_report`).

        We define the **CODECOV_IO_UPLOAD_TOKEN** environment variable
        to avoid to skip the step.  It's the default behaviour if we
        don't give this variable to Eve.

        """

        if not os.environ.get('CODECOV_IO_UPLOAD_TOKEN'):
            self.codecov_io_server = CodecovIOMockServer()
            self.codecov_io_server.start()

            os.environ.update({
                'CODECOV_IO_BASE_URL': self.codecov_io_server.url,
                'CODECOV_IO_UPLOAD_TOKEN': 'FAKE_TOKEN',
            })  # yapf: disable

        self.cluster = Cluster()
        for master in self.cluster._masters.values():
            master.conf['CODECOV_IO_BASE_URL'] = self.codecov_io_server.url
            master.conf['CODECOV_IO_UPLOAD_TOKEN'] = 'FAKETOKEN'
        self.cluster.start()
        self.local_repo = self.cluster.clone()
        super(TestPublishCodeCoverage, self).setUp()

    def tearDown(self):
        """Stop the ``codecov.io`` mock HTTP server if needed.

        And restore old environment variables.

        """
        super(TestPublishCodeCoverage, self).tearDown()

        if self.codecov_io_server:
            self.codecov_io_server.stop()
            self.codecov_io_server = None

        for varname_suffix in ['BASE_URL', 'UPLOAD_TOKEN']:
            varname = 'CODECOV_IO_{0}'.format(varname_suffix)
            if varname in os.environ:
                del os.environ[varname]
        self.cluster.stop()

    def _get_publish_codecov_build(self, builder_name='test_docker_builder'):
        """Search the build of the code coverage report publication step.

        Args:
            builder_name: Root builder name rather than bootstrap.

        Returns:
            None if no potential build else the build found.

        """
        builders = self.cluster.api.get(
            'builders?name__contains={0}'.format(builder_name))
        for builder in builders['builders']:
            builds_url = 'builders/{0}/builds'.format(builder['builderid'])
            builds = self.cluster.api.get(builds_url)
            for build in builds['builds']:
                steps = self.cluster.api.get(
                    '{0}/{1}/steps?name__contains=coverage'.format(
                        builds_url, build['number']))
                if steps:
                    return build
        return None

    def test_codecovio_success(self):
        """Test PublishCoverageReport success.

        If we use the mock HTTP server, we ensure that we execute the
        requests with the correct query parameters and headers, in
        accordance with the ``codecov.io`` API (see
        https://docs.codecov.io/v4.3.0/reference#upload).

        """

        import xml.etree.cElementTree as ET

        coverage = ET.Element('coverage', {
            'branch-rate': '0',
            'line-rate': '0',
            'timestamp': 'XXXXXXXXXXXXX',
            'version': '4.3.4',
        })

        sources = ET.SubElement(coverage, 'sources')
        ET.SubElement(sources, 'source').text = '/srv/test_codecov_io'

        packages = ET.SubElement(coverage, 'packages')
        pacakge = ET.SubElement(packages, 'package', {
            'branch-rate': '0',
            'complexity': '0',
            'line-rate': '0',
            'name': '.',
        })

        classes = ET.SubElement(pacakge, 'classes')
        class_ = ET.SubElement(classes, 'class', {
            'branch-rate': '0',
            'complexity': '0',
            'filename': 'test.py',
            'line-rate': '0',
            'name': 'test.py'
        })

        # Based on https://raw.githubusercontent.com/cobertura/web/
        # f0366e5e2cf18f111cbd61fc34ef720a6584ba02/htdocs/xml/coverage-03.dtd

        ET.SubElement(class_, 'methods')
        lines = ET.SubElement(class_, 'lines')
        for i in [3, 4, 5, 7, 8]:
            ET.SubElement(lines, 'line', {'hits': '0', 'number': str(i)})

        report_file = '/tmp/coverage.xml'
        tree = ET.ElementTree(coverage)
        tree.write(report_file, encoding='utf-8', xml_declaration=True)

        self.local_repo.push(yaml=PreMerge(steps=[{
            'SetProperty': {
                'name': 'set property my_revision',
                'property': 'my_revision',
                'value': '98f9379054719da6e7b5fd537b5a8e0ede096968',
            }
        }, {
            'PublishCoverageReport': {
                'repository': 'scality/test_codecov_io',
                'revision': '%(prop:my_revision)s',
                'filepaths': [report_file],
                'branch': 'master',
                'uploadName': 'ucheck',
                'configFile': '.codecov.yml',
            }
        }]))

        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        assert buildset.result == 'success'

        build = buildset.buildrequest.build
        child_buildsets = build.children
        assert len(child_buildsets) == 1
        child_build = child_buildsets[0].buildrequest.build
        assert child_build.result == 'success'

        if self.codecov_io_server is None:
            return

        self.codecov_io_server.assert_request_received_with(
            ('POST', '/upload/v4', {
                'commit':
                '98f9379054719da6e7b5fd537b5a8e0ede096968',
                'token':
                'FAKETOKEN',
                'build':
                build.number,
                'build_url':
                '{0}#builders/{1}/builds/{2}'.format(self.cluster.api.url,
                                                     child_build.builderid,
                                                     child_build.number),
                'service':
                'buildbot',
                'branch':
                'master',
                'name':
                'ucheck',
                'slug':
                'scality/test_codecov_io',
                'yaml':
                '.codecov.yml',
            }, {
                'Accept': 'text/plain',
            }), ('PUT', '/s3/fake_report.txt', {
                'AWSAccessKeyId': 'FAKEAWSACCESSKID',
                'Expires': str(self.codecov_io_server.expires),
                'Signature': 'FAKESIGNATURE',
            }, {
                'Content-Length': str(os.path.getsize(report_file)),
                'Content-Type': 'text/plain',
                'x-amz-acl': 'public-read',
                'x-amz-storage-class': 'REDUCED_REDUNDANCY',
            }))
