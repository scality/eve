"""Class to generate an SQLite database path and sqlalchemy URL"""

from __future__ import print_function

import os

from tests.util.daemon import Daemon


class Sqlite(Daemon):
    def __init__(self, **_):
        """
        Class to generate an SQLite database path and sqlalchemy URL
        Args:
            **_: ignored
        """
        super(Sqlite, self).__init__(name='sqlite')
        self.url = \
            'sqlite:///' + os.path.join(self._base_path, 'state.sqlite')

    def start(self):
        """
        Fake method to make this class have the same interfaces as other
        daemons (e.g., MySQL)
        """
