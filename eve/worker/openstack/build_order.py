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


class OpenStackBuildOrder(util.BaseBuildOrder):
    """Base class representing a build to trigger on an OpenStack instance.

    Scheduler, properties and OpenStack config.

    """

    DEFAULT_IMAGE = 'Ubuntu 14.04 LTS (Trusty Tahr) (PVHVM)'
    DEFAULT_FLAVOR = 'general1-4'
    """See https://developer.rackspace.com/docs/cloud-servers/v2/general-api-info/flavors/."""  # noqa: E501, pylint: disable=line-too-long

    def setup_properties(self):
        super(OpenStackBuildOrder, self).setup_properties()

        self.properties.update({
            'worker_path': self._worker['path'],
            'openstack_image': self._worker.get('image', self.DEFAULT_IMAGE),
            'openstack_flavor': self._worker.get('flavor', self.DEFAULT_FLAVOR)
        })
