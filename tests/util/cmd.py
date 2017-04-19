# coding: utf-8
"""A set of utilities used by EVE deployment tools."""
import logging
import os
import subprocess

logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)


def cmd(command, ignore_exception=False, cwd=None, wait=True, env=None):
    """Execute a shell command and display output in a readable manner."""
    output = ''
    logger.info('COMMAND : %s', command)
    if env is not None:
        for key, val in env.iteritems():
            os.environ[key] = val
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd)

    if not wait:
        return None

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline:
            logger.info(' │ %s', nextline.rstrip())
            output += nextline
        elif process.poll() is not None:
            break

    logger.info(u' └────────')

    process.communicate()
    exit_code = process.returncode

    if exit_code == 0 or ignore_exception:
        return output
    raise subprocess.CalledProcessError(exit_code, command)
