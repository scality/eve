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

from unittest import TestCase

from tests.util.buildbot_master.buildbot_master import BuildbotMaster
from tests.util.daemon import Daemon


class TestMaster(TestCase):
    def test_start_and_stop_master(self):
        """Test start and stop a buildbot master.

        Steps:
            - Start a standalon buildmaster.
            - Look for a line in the code to check if it completed its start.
            - Stop it.
            - Look for a line in the code to check if it completed its stop.

        """
        ports = Daemon.get_free_port(3)
        conf = dict(
            ARTIFACTS_PUBLIC_URL='None',
            DB_URL='sqlite:///state.sqlite',
            DOCKER_API_VERSION='1.25',
            EXTERNAL_URL='http://example.com/',
            GIT_HOST='mock',
            GIT_OWNER='repo_owner',
            GIT_REPO='something',
            GIT_SLUG='test',
            HTTP_PORT=str(ports[0]),
            MASTER_FQDN='localhost',
            MASTER_MODE='standalone',
            MASTER_NAME='buildmaster',
            PB_PORT=str(ports[1]),
            PROJECT_URL='www.example.com',
            SUFFIX='test_suffix',
            TRY_PORT=str(ports[2]),
            WAMP_REALM='realm1',
            WAMP_ROUTER_URL='ws://localhost:1234/ws'
        )

        master = BuildbotMaster(conf)
        master.start()
        self.assertIn('BuildMaster is running', master.loglines[-1],
                      'BuildMaster is not running')
        master.stop()
        self.assertIn('Server Shut Down.', master.loglines[-1],
                      'BuildMaster didn\'t properly shut down')
