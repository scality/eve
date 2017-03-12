from functools import wraps

from buildbot.process.properties import Interpolate
from twisted.internet import defer


def hide_interpolatable_name(func):
    """Hide the interpolatable name to be later rendered."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self._interpolatable_name = kwargs.pop('name', None) or self.name
        self.name = str(self._interpolatable_name)
        return func(self, *args, **kwargs)
    return wrapper


def render_interpolatable_name(func):
    """Render the hidden interpolatable name before proceeding."""
    @wraps(func)
    @defer.inlineCallbacks
    def wrapper(self, *args, **kwargs):
        if isinstance(self._interpolatable_name, Interpolate):
            finished = self.build.render(self._interpolatable_name)

            def set_name(res):
                self.name = res
            finished.addCallback(set_name)
            yield finished
        res = yield func(self, *args, **kwargs)
        defer.returnValue(res)
    return wrapper
