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


from buildbot.plugins import util
from buildbot.process.properties import Interpolate


def get_artifacts_base_name():
    """Give containing the base name of artifacts container."""
    return (
        '%(prop:git_host)s:%(prop:git_owner)s:%(prop:git_slug)s:'
        + util.env.ARTIFACTS_PREFIX
        + '%(prop:product_version)s.r%(prop:commit_timestamp)s'
        + '.%(prop:commit_short_revision)s'
    )


def get_artifacts_name(buildnumber, stage_name):
    """Give interpolate containing the full name of artifacts container."""
    b4nb = buildnumber.zfill(8)
    return Interpolate(
        get_artifacts_base_name()
        + '.' + stage_name + '.' + b4nb
    )
