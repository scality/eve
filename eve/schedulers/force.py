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

import subprocess

from buildbot.schedulers.forcesched import ForceScheduler, ValidationError
from twisted.internet import defer, threads


class EveForceScheduler(ForceScheduler):
    @defer.inlineCallbacks
    def gatherPropertiesAndChanges(self, collector, **kwargs):
        properties, changeids, sourcestamps = \
            yield super(EveForceScheduler, self).gatherPropertiesAndChanges(
                collector, **kwargs
            )

        yield collector.collectValidationErrors('branch',
                                                self.add_missing_revisions,
                                                sourcestamps)

        defer.returnValue((properties, changeids, sourcestamps))

    @staticmethod
    @defer.inlineCallbacks
    def add_missing_revisions(sourcestamps):
        for _, sourcestamp in sourcestamps.items():
            if not sourcestamp['revision']:
                # Retrieve revision from branch for sourcestamps without one
                res = yield threads.deferToThread(
                    subprocess.check_output,
                    ['git', 'ls-remote', sourcestamp['repository'],
                     sourcestamp['branch']],
                    stderr=subprocess.PIPE,
                )
                try:
                    sourcestamp['revision'] = res.split()[0].decode('utf-8')
                except IndexError:
                    raise ValidationError("'%s' branch not found" %
                                          sourcestamp['branch'])
