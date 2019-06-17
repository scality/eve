# Copyright 2019 Scality
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

import sqlalchemy as sa
from buildbot.db.logs import LogsConnectorComponent


def deleteOldLogChunks(self, older_than_timestamp):
    def thddeleteOldLogs(conn):
        model = self.db.model
        res = conn.execute(sa.select([sa.func.count(model.logchunks.c.content)]))  # noqa: E501
        count1 = res.fetchone()[0]
        res.close()

        # update log types older than timestamps
        # we do it first to avoid having UI discrepancy

        # N.B.: we utilize the fact that steps.id is auto-increment, thus steps.started_at # noqa: E501
        # times are effectively sorted and we only need to find the steps.id at the upper # noqa: E501
        # bound of steps to update.

        # SELECT steps.id from steps WHERE steps.started_at < older_than_timestamp ORDER BY steps.id DESC LIMIT 1; # noqa: E501
        res = conn.execute(
            sa.select([model.steps.c.id])
            .where(model.steps.c.started_at < older_than_timestamp)
            .order_by(model.steps.c.id.desc())
            .limit(1)
        )
        stepid_max = res.fetchone()[0]
        res.close()

        # UPDATE logs SET logs.type = 'd' WHERE logs.stepid <= stepid_max;
        res = conn.execute(
            model.logs.update()
            .where(model.logs.c.stepid <= stepid_max)
            .values(type='d')
        )
        res.close()

        # query all logs with type 'd' and delete their chunks.
        q = sa.select([model.logs.c.id])
        q = q.select_from(model.logs)
        q = q.where(model.logs.c.type == 'd')

        # delete their logchunks
        res = conn.execute(
            model.logchunks.delete()
            .where(model.logchunks.c.logid.in_(q))
        )
        res.close()
        res = conn.execute(sa.select([sa.func.count(model.logchunks.c.content)]))  # noqa: E501
        count2 = res.fetchone()[0]
        res.close()
        return count1 - count2
    return self.db.pool.do(thddeleteOldLogs)


def patch():
    LogsConnectorComponent.deleteOldLogChunks = deleteOldLogChunks
