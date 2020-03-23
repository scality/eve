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

"""Utility functions for buildbot workers."""


def compute_instance_name(build):
    """Compute an instance name and returns it.

    Utility function designed to retrieve worker build properties to create a
    instance name that is different on every worker.
    The main idea is to create a instance name that can allow us to identify
    the worker and also to avoid reusing worker's name so that there's no risk
    of encountering any kind of collison issue.
    """

    name = build.getProperty('workername').replace('_', '-')
    buildid = build.getProperty('buildnumber')
    buildnumber = build.getProperty('bootstrap')
    return '{name}-{buildnumber}-{buildid}'.format(
        name=name,
        buildnumber=buildnumber,
        buildid=buildid
    )
