# Copyright 2019 Scality
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

"""This test suite checks the Configurators setup in Eve."""

import unittest

from buildbot.configurators.janitor import JANITOR_NAME
from buildbot.process.results import SUCCESS

from tests.util.cluster import Cluster


class TestJanitor(unittest.TestCase):
    def test_janitor(self):
        """Test a cluster with the Janitor configurator.

        Steps:
        - Configure the Janitor to build every day and every minute.
        - Wait for the Janitor to do his job.
        - Ensure the build succeeded

        """
        conf = {
            'JANITOR_DAY': '*',
            'JANITOR_HOUR': '*',
            'JANITOR_MINUTE': '*',
            'JANITOR_DAY_RETENTION': '1'
        }
        with Cluster(extra_conf=conf) as cluster:
            build = cluster.api.get_finished_build(JANITOR_NAME, timeout=120)
            self.assertEqual(build['results'], SUCCESS)
