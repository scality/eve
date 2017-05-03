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


class TestMaster(TestCase):
    def test_start_and_stop_master(self):
        """Test start and stop a buildbot master.

        Steps:
            - start a standalon buildmaster
            - look for a line in the code to check if it completed its start
            - stop it
            - look for a line in the code to check if it completed its stop
        """
        master = BuildbotMaster(mode='standalone', git_repo='something')
        master.start()
        assert 'BuildMaster is running' in master.loglines[-1]
        master.stop()
        assert 'Server Shut Down.' in master.loglines[-1]
