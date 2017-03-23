"""HACK to fix a bug where the git diff is sent as an str instead of
unicode and triggers an exception."""
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
