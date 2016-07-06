#coding: utf-8
"""A set of utilities used by EVE deployment tools."""
from __future__ import print_function

import subprocess
import sys


def cmd(command, ignore_exception=False):
    """Execute a shell command and display output in a readable manner."""
    log = ''
    print('\nCOMMAND : %s' % command)
    process = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(' | ' + nextline)
        sys.stdout.flush()
        log += nextline

    print(u' L________')

    process.communicate()
    exit_code = process.returncode

    if exit_code == 0 or ignore_exception:
        return log
    raise subprocess.CalledProcessError(exit_code, command)
