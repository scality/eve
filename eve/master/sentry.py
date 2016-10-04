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
