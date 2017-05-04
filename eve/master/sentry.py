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

"""Utils to log errors to sentry."""

from raven import Client
from raven.transport.twisted import TwistedHTTPTransport
from twisted.logger import ILogObserver, globalLogPublisher
from zope.interface import provider


def init_sentry_logging(sentry_dsn):
    """Start logging of all failure to sentry."""
    client = Client(sentry_dsn,
                    transport=TwistedHTTPTransport,
                    auto_log_stacks=True)

    @provider(ILogObserver)
    def log_to_sentry(event):
        """Log a failure to Sentry."""
        if not event.get('isError') or 'failure' not in event:
            return
        failure = event['failure']
        client.captureException((failure.type, failure.value,
                                 failure.getTracebackObject()))

    globalLogPublisher.addObserver(log_to_sentry)
