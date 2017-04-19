import json
import os


class CrossbarConfFactory(object):
    master_count = 0

    def __init__(self, port=None):
        json_conf_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'crossbar.json')

        with open(json_conf_path) as fhandle:
            self._conf = json.load(fhandle)
        if port is not None:
            self._conf['workers'][0]['transports'][0]['endpoint']['port'] = \
                port

    def dump(self, filename):
        with open(filename, 'w') as fhandle:
            json.dump(self._conf, fhandle)
