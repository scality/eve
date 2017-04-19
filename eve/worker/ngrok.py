"""Allow workers to access local test eve instance."""

import json
import re
import time
from os import path
from subprocess import PIPE, Popen


# #########################
# Ngrok
# #########################

class NgrokNotAvailableError(Exception):
    """ngrok binary could not be found."""


class NgrokTimeoutError(Exception):
    """ngrok took too much time to create the tunnel."""


class Ngrok(object):
    """ngrok utility wrapper"""

    MAX_WAIT_TUNNEL = 5
    URL_REGEXP = re.compile(r'URL:\w+://(\S+):(\d+)')

    def __init__(self, command='ngrok'):
        super(Ngrok, self).__init__()
        self.command = path.expanduser(command)
        self._proc = None
        self._state = None

    def start(self, protocol, port, region='us'):
        """Start ngrok and returns tunnel url and port.

        Args:
            protocol: str: ngrok tunnel protocol on host
            port: str: ngrok tunel port on host
            region: str: --region ngrok option

        Returns: tuple (str, str) : (url, port)

        Raises:
            * NgrokNotAvailableError
            * NgrokTimeoutError

        """
        command = [
            self.command, str(protocol), str(port),
            '--log', 'stdout', '--log-level', 'debug', '--log-format', 'json',
            '--region', region
        ]

        try:
            proc = Popen(command, stdout=PIPE)
        except OSError as error:
            raise NgrokNotAvailableError(
                "Couldn't start ngrok with command: '%s' : '%s'."
                "Is Ngrok in the PATH ?" %
                (command, error)
            )

        start = time.time()
        while not proc.poll() and time.time() - start < self.MAX_WAIT_TUNNEL:
            stdout = proc.stdout.readline()
            if not stdout:
                time.sleep(0.1)
                continue
            data = json.loads(stdout)
            if 'resp' in data:
                match = self.URL_REGEXP.search(data['resp'])
                if match:
                    self._proc = proc
                    self._state = (match.group(1), match.group(2))
                    return self._state

        # we reached the MAX_WAIT_TUNNEL timeout. end process and raise error
        proc.terminate()
        raise NgrokTimeoutError(
            'Ngrock took more than the %s max seconds'
            ' to return tunnel specifications. Aborted.' %
            self.MAX_WAIT_TUNNEL)

    @property
    def running(self):
        """Returns: boolean: True if ngrok is running."""
        return self._state is not None

    def stop(self):
        """Stop ngrok, if started."""
        if self.running:
            self._proc.terminate()
            self._proc = None
            self._state = None

    def __del__(self):
        self.stop()
