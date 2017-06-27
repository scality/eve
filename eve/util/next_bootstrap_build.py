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

import re

from buildbot.plugins import util


def nextBootstrapBuild(bldr, requests):
    if util.env.LOW_PRIORITY_BRANCH:
        for request in requests:
            if not re.match(util.env.LOW_PRIORITY_BRANCH,
                            request.source.branch):
                return request
    return requests[0]
