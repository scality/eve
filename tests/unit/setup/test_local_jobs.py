import shutil
import unittest
from collections import namedtuple
from tempfile import mkdtemp, mktemp

import eve.setup.local_jobs
from buildbot.plugins import util
from tests.util.yaml_factory import LocalJobsYaml

DumbWorker = namedtuple('DumbWorker', ['name'])


class SetupLocalJobsTest(unittest.TestCase):
    def setUp(self):
        """
        Set up the environments for the tests.

        Steps:
            - Set a fake environment
            - Create a fake yaml file
        """
        self.tmpdir = mkdtemp()
        util.env = util.load_env([
            ('LOCAL_JOBS_DIRPATH', self.tmpdir),
            ('SUFFIX', '_foo'),
        ])
        self.yaml = LocalJobsYaml()
        self.filename = mktemp(dir=self.tmpdir)
        self.yaml.filedump(self.filename)

    def tearDown(self):
        """
        Remove the environment for the tests.
        """
        shutil.rmtree(self.tmpdir)

    def test_local_jobs(self):
        """
        Test the local_jobs function twice: without any exception thrown
        and with an exception thrown.
        """
        # yapf: disable
        self.assertTrue(eve.setup.local_jobs.local_jobs(
            [DumbWorker(name='foo')]) is not None)

        # When there is no job, a generic exception is thrown
        with self.assertRaises(Exception):
            eve.setup.local_jobs.local_jobs([])
