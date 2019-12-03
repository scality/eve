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

from os.path import abspath, dirname, join

import os

import yaml


class ConfigurableStepMixin():
    """Base class for a step that access the setting in the main.yml."""

    def getEveConfig(self):
        """Load Eve's config file on the master and returns the data."""
        implicit_config = {}
        try:
            implicit_conf = join(dirname(dirname(abspath(__file__))),
                                 'etc', 'implicit-stages.yml')
            with open(implicit_conf) as config_file:
                implicit_config = yaml.load(config_file.read())
        except yaml.YAMLError:
            raise
        try:
            conf = os.path.expanduser(self.getProperty('conf_path'))
            with open(conf) as config_file:
                config = yaml.load(config_file.read())
                if type(config) is dict:
                    for key in implicit_config['stages']:
                        config['stages'][key] = implicit_config['stages'][key]
                return config
        except yaml.YAMLError:
            raise
