#!/usr/bin/env python

import argparse
import os


# From Russell Heilling: http://stackoverflow.com/a/10551190
class EnvDefault(argparse.Action):  # pylint: disable=R0903

    def __init__(self, envvar, required=False, default=None, **kwargs):
        # Overriding default with environment variable if available
        if envvar in os.environ:
            default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required,
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
