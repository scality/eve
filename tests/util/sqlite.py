# coding: utf-8
"""This test suite checks end-to-end operation of EVE."""

from __future__ import print_function

import os

from tests.util.daemon import Daemon


class Sqlite(Daemon):
    def __init__(self, **_):
        super(Sqlite, self).__init__(name='sqlite')
        self.url = \
            'sqlite:///' + os.path.join(self._base_path, 'state.sqlite')

    def start(self):
        pass
