# coding: utf-8
"""A set of utilities used by EVE deployment tools."""
import logging
import subprocess

logger = logging.getLogger(__name__)


def cmd(command, ignore_exception=False):
    """Execute a shell command and display output in a readable manner."""
    output = ''
    logger.info('COMMAND : %s', command)
    process = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline:
            logger.info(' │ %s', nextline.strip())
            output += nextline
        elif process.poll() is not None:
            break

    logger.info(u' └────────')

    process.communicate()
    exit_code = process.returncode

    if exit_code == 0 or ignore_exception:
        return output
    raise subprocess.CalledProcessError(exit_code, command)
