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

"""Step patching feature."""

import yaml
from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SKIPPED, SUCCESS, WARNINGS
from twisted.internet import defer
from twisted.logger import Logger


class StepPatcherConfig(BuildStep):
    """Parses the patch config file and sets the corresponding property.

    The config file path should be set in the conf_path argument.
    If this variable is not set, the step patching feature is
    disabled.

    """
    name = 'step patcher config'
    logger = Logger('eve.steps.StepPatcherReader')

    def __init__(self, conf_path=None, **kwargs):
        kwargs.setdefault('haltOnFailure', False)
        super(StepPatcherConfig, self).__init__(**kwargs)
        self.conf_path = conf_path

    def run(self):
        prop = 'step_patcher_config'
        config = {}
        try:
            with open(self.conf_path) as patch_file:
                config = yaml.load(patch_file.read())
        except (OSError, IOError, yaml.YAMLError) as err:
            self.logger.error(
                'An error occured while loading the patcher config file at '
                '{path}: {err}', path=self.conf_path, err=err)
            self.setProperty(prop, {}, 'StepPatcherConfig')
            return defer.succeed(SKIPPED)

        self.setProperty('step_patcher_config', config, 'StepPatcherConfig')
        if not config:
            return defer.succeed(SUCCESS)
        else:
            self.logger.info("Setting patching config: {conf}",
                             conf=config)
            return defer.succeed(WARNINGS)
