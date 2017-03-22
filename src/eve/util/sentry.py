"""Utils to log errors to sentry."""

from buildbot.plugins import util
from raven import Client
from raven.transport.twisted import TwistedHTTPTransport
from twisted.logger import ILogObserver, globalLogPublisher
from zope.interface import provider


def init_sentry_logging():
    """Start logging of all failure to sentry."""
    if not util.env.SENTRY_DSN:
        return
    client = Client(util.env.SENTRY_DSN,
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
