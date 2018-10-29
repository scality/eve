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

import os.path

from buildbot.plugins import util


class HeatOpenStackBuildOrder(util.BaseBuildOrder):
    """Base class representing a build to trigger on an OpenStack instance.

    Scheduler, properties and OpenStack config.

    """

    def read_worker_scripts(self):
        for script in ['init.sh', 'requirements.sh', 'start.sh']:
            file_ = "%s/build/%s/%s" % (
                self.properties['master_builddir'][0],
                self._worker['path'],
                script)

            contents = ''
            if os.path.isfile(file_):
                contents = open(file_).read()

            self.properties.update({script: (contents, 'OpenstackBuildOrder')})

    def setup_properties(self):
        super(HeatOpenStackBuildOrder, self).setup_properties()
        worker_path = self._worker.get('path', '')

        if worker_path:
            self.read_worker_scripts()

        self.properties.update({
            'worker_path': (worker_path, 'OpenstackBuildOrder'),
            'openstack_image': (self._worker.get('image', ''),
                                'OpenstackBuildOrder'),
            'openstack_flavor': (self._worker.get('flavor', ''),
                                 'OpenstackBuildOrder'),
        })
