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

from buildbot.plugins import util
from buildbot.process.results import SKIPPED, SUCCESS


def hideStepIf(result, hidden_results):
    if not util.env.HIDE_INTERNAL_STEPS:
        return False
    return result in hidden_results


def hideStepIfSuccess(result, step):
    return hideStepIf(result, [SUCCESS])


def hideStepIfSkipped(result, step):
    return hideStepIf(result, [SKIPPED])


def hideStepIfSuccessOrSkipped(result, step):
    return hideStepIf(result, [SUCCESS, SKIPPED])
