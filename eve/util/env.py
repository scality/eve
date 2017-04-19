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

from os import environ

SETTINGS = {}
SECRETS = {}


class Settings(dict):
    def __init__(self, variables):
        super(Settings, self).__init__()

        def no_conversion(value):
            return value

        for var in variables:
            assert isinstance(var, tuple), "%s is not a tuple" % var
            name = var[0]
            try:
                default = var[1]
            except IndexError:
                default = None
            try:
                convert = var[2]
            except IndexError:
                convert = no_conversion
            self.load(name, default, convert)

    def load(self, name, default, convert):
        try:
            value = environ[name]
        except KeyError:
            if default is None:
                raise
            value = default
        self[name] = convert(value)

    def __getattr__(self, name):
        return self[name]


def filter_secrets():
    for key in dict(environ):
        if key.startswith('SECRET_'):
            SECRETS[key.lstrip('SECRET_')] = environ.pop(key)


def get_secrets():
    return SECRETS


def load_env(variables):
    global SETTINGS  # pylint: disable=global-statement
    SETTINGS = Settings(variables)
    filter_secrets()
    return SETTINGS
