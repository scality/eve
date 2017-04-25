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
            return defer.succeed(SKIPPED)

        self.setProperty('step_patcher_config', config, 'StepPatcherConfig')
        if not config:
            return defer.succeed(SUCCESS)
        else:
            self.logger.info("Setting patching config: {conf}",
                             conf=config)
            return defer.succeed(WARNINGS)
