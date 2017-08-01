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
"""Hack to prevent housekeeping from retry sub-build."""
import buildbot.data.masters
from buildbot.process.results import CANCELLED
from twisted.internet import defer


def cancelRetryForSubBuilds(func):
    @defer.inlineCallbacks
    def wrap(self, masterid, name):
        buildrequests = yield self.master.db.buildrequests.getBuildRequests(
            complete=False, claimed=masterid)
        brids = [br['buildrequestid'] for br in buildrequests
                 if br['waited_for'] is True]
        yield func(self, masterid, name)
        yield self.master.db.buildrequests.completeBuildRequests(
            brids, CANCELLED)

    return wrap


def patch():
    buildbot.data.masters.RETRY = CANCELLED
    buildbot.data.masters.Master._masterDeactivatedHousekeeping = \
        cancelRetryForSubBuilds(
            buildbot.data.masters.Master._masterDeactivatedHousekeeping)
