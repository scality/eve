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
"""Hack to fix a bug where the git diff is sent as str instead of unicode."""

from buildbot.process import buildrequest


class TempSourceStamp(object):
    def asDict(self):  # pylint: disable=invalid-name,missing-docstring
        result = vars(self).copy()
        del result['ssid']
        del result['changes']
        if 'patch' in result and result['patch'] is None:
            result['patch'] = (None, None, None)
        result['patch_level'], result['patch_body'], result[
            'patch_subdir'] = result.pop('patch')
        result['patch_author'], result[
            'patch_comment'] = result.pop('patch_info')
        assert all(
            isinstance(val, (str, unicode, type(None), int))  # added str here
            for attr, val in result.items()
        ), result
        return result


def patch():
    buildrequest.TempSourceStamp = TempSourceStamp
