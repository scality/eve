"""Step patching feature."""
import re

from twisted.logger import Logger


class StepPatcher(object):
    """Generic hook to patch step types and parameters."""

    logger = Logger('eve.steps.StepPatcher')

    def __init__(self, config=None):
        config = config or {}
        self.logger.info("Running with conf {conf}", conf=config)
        skip_tests = config.get('skip_steps', [])
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

        name = params.get('name', '')
        self.logger.info("name: {name} regexp: {regexp}", name=name,
                         regexp=self.skip_regexp)
        if name and self.skip_regexp.match(name):
            params['doStepIf'] = False
            params['descriptionDone'] = 'Temporarily disabled'

        return step_type, params
