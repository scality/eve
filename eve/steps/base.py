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

import os

import yaml


class ConfigurableStepMixin():
    """Base class for a step that access the setting in the main.yml."""

    def getEveConfig(self):
        """Load Eve's config file on the master and returns the data."""
        try:
            conf = os.path.expanduser(self.getProperty('conf_path'))
            with open(conf) as config_file:
                config = yaml.load(config_file.read())
                return config
        except yaml.YAMLError:
            raise
