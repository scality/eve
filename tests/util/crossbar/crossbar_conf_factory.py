import json
import os


class CrossbarConfFactory(object):
    master_count = 0

    def __init__(self, port=None):
        """
        Class to generate Crossbar configuration
        Args:
            port: the port number to use (optional)
        """
        json_conf_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'crossbar.json')

        with open(json_conf_path) as fhandle:
            self._conf = json.load(fhandle)
        if port is not None:
            self._conf['workers'][0]['transports'][0]['endpoint']['port'] = \
                port

    def dump(self, filename):
        """
        Dumps the conf to a file
        Args:
            filename (str): the file path to dump the conf to
        """
        with open(filename, 'w') as fhandle:
            json.dump(self._conf, fhandle)
