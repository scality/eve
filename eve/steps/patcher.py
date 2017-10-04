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
"""Patching feature."""

import re

import yaml
from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SKIPPED, SUCCESS, WARNINGS
from twisted.internet import defer
from twisted.logger import Logger


class PatcherConfig(BuildStep):
    """Parse the patch config file and sets the corresponding property.

    The config file path should be set in the conf_path argument.
    If this variable is not set, the step patching feature is
    disabled.

    """

    name = 'read patcher config'
    logger = Logger('eve.steps.PatcherConfig')

    def __init__(self, conf_path=None, **kwargs):
        kwargs.setdefault('haltOnFailure', False)
        super(PatcherConfig, self).__init__(**kwargs)
        self.conf_path = conf_path

    def run(self):
        prop = 'patcher_config'
        config = {}
        try:
            with open(self.conf_path) as patch_file:
                config = yaml.load(patch_file.read())
        except (OSError, IOError, yaml.YAMLError) as err:
            self.logger.error(
                'An error occured while loading the patcher config file at '
                '{path}: {err}', path=self.conf_path, err=err)
            self.setProperty(prop, {}, 'PatcherConfig')
            return defer.succeed(SKIPPED)

        self.setProperty('patcher_config', config, 'PatcherConfig')
        if not config:
            return defer.succeed(SUCCESS)

        self.logger.info("Setting patching config: {conf}", conf=config)
        return defer.succeed(WARNINGS)


class Patcher(object):
    """Generic hook to patch branches and steps."""

    logger = Logger('eve.steps.Patcher')

    def __init__(self, config=None):
        config = config or {}
        self.logger.info("Running with conf {conf}", conf=config)

        self.steps_regexp = self._parse_config(
            config.get('skip_steps', []))
        self.branches_regexp = self._parse_config(
            config.get('skip_branches', []))

    def _parse_config(self, skip_data):
        """Read a section of the config file and output a compiled regexp.

        Args:
            skip_data (str, list): individual regexps to skip.

        """
        if not skip_data:
            return None

        elif isinstance(skip_data, basestring):
            try:
                return re.compile(skip_data)
            except re.error as err:
                self.logger.error(
                    "Couldn't compile a regexp from '{regexp}': {err}",
                    regexp=skip_data, err=err
                )

        elif isinstance(skip_data, (list, tuple)):
            try:
                return re.compile('|'.join(skip_data))
            except (TypeError, re.error) as err:
                self.logger.error(
                    "Couldn't compile a master regexp from '{regexp}': {err}",
                    regexp=skip_data, err=err
                )

    def patch_step(self, step_type, params):
        if not self.steps_regexp:
            return step_type, params

        name = params.get('name', '')
        self.logger.info("name: {name} regexp: {regexp}", name=name,
                         regexp=self.steps_regexp)
        if name and self.steps_regexp.match(name):
            params['doStepIf'] = False
            params['descriptionDone'] = 'Temporarily disabled'

        return step_type, params

    def is_branch_skipped(self, branch):
        if not self.branches_regexp:
            return False

        self.logger.info("branch: {branch} regexp: {regexp}", branch=branch,
                         regexp=self.branches_regexp)
        if branch and self.branches_regexp.match(branch):
            return True

        return False
