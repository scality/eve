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

from buildbot.db.builds import BuildsConnectorComponent
from twisted.internet import defer


@defer.inlineCallbacks
def getPrevSuccessfulBuild(self, builderid, number, ssBuild):
    gssfb = self.master.db.sourcestamps.getSourceStampsForBuild
    rv = None
    tbl = self.db.model.builds
    offset = 0
    increment = 1000
    matchssBuild = set([(ss['repository'],
                         ss['branch'],
                         ss['codebase']) for ss in ssBuild])
    while rv is None:
        # Get some recent successful builds on the same builder
        prevBuilds = yield self._getRecentBuilds(whereclause=((tbl.c.builderid == builderid) &  # noqa: E501
                                                              (tbl.c.number < number) &  # noqa: E501
                                                              (tbl.c.results == 0)),  # noqa: E501
                                                 offset=offset,
                                                 limit=increment)
        if not prevBuilds:
            break
        for prevBuild in prevBuilds:
            prevssBuild = set([(ss['repository'],
                                ss['branch'],
                                ss['codebase']) for ss in (yield gssfb(prevBuild['id']))])  # noqa: E501
            if prevssBuild == matchssBuild:
                # A successful build with the same
                # repository/branch/codebase was found !
                rv = prevBuild
                break
        offset += increment

    return rv


def patch():

    BuildsConnectorComponent.getPrevSuccessfulBuild = getPrevSuccessfulBuild
