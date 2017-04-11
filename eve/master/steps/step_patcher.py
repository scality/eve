"""Step patching feature."""

import re
import yaml

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import (
    FAILURE, SUCCESS, SKIPPED, WARNINGS
)

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
        if not self.conf_path:
            self.logger.debug('PATCHER_FILE_PATH is not set. Skipping')
            self.setProperty(prop, {}, 'StepPatcherConfig')
            return defer.succeed(SKIPPED)

        config = {}
        try:
            with open(self.conf_path) as patch_file:
                config = yaml.load(patch_file.read())
        except (OSError, IOError, yaml.YAMLError) as err:
            self.logger.error(
                'An error occured while loading the patcher config file at '
                '{path}: {err}', path=self.conf_path, err=err)
            self.setProperty(prop, {}, 'StepPatcherConfig')
            return defer.succeed(FAILURE)

        self.setProperty('step_patcher_config', config, 'StepPatcherConfig')
        if not config:
            return defer.succeed(SUCCESS)
        else:
            self.logger.info("Setting patching config: {conf}",
                             conf=config)
            return defer.succeed(WARNINGS)


class StepPatcher(object):
    """Generic hook to patch step types and parameters."""

    logger = Logger('eve.steps.StepPatcher')

    def __init__(self, config=None):
        config = config or {}
        skip_tests = config.get('skip_tests', [])
        self.skip_regexp = None
        if not skip_tests:
            return

        if isinstance(skip_tests, basestring):
            try:
                self.skip_regexp = re.compile(skip_tests)
            except re.error as err:
                self.logger.error(
                    "Couldn't compile a regexp from '{regexp}': {err}",
                    regexp=skip_tests, err=err
                )
        elif isinstance(skip_tests, (list, tuple)):
            try:
                self.skip_regexp = re.compile('|'.join(skip_tests))
            except (TypeError, re.error) as err:
                self.logger.error(
                    "Couldn't compile a master regexp from '{regexp}': {err}",
                    regexp=skip_tests, err=err
                )

    def patch(self, step_type, params):
        if not self.skip_regexp:
            return step_type, params

        if self.skip_regexp.match(params.get('name', '')):
            params['doStepIf'] = False
            params['descriptionDone'] = 'Temporarily disabled'

        return step_type, params
