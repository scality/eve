# coding: utf-8

# Copyright 2017 Scality
#
# This file is part of Eve.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.

"""A set of utilities used by EVE deployment tools."""
import logging
import subprocess

logger = logging.getLogger(__name__)


def cmd(command, ignore_exception=False, cwd=None, wait=True):
    """Execute a shell command and display output in a readable manner."""
    output = ''
    logger.info('COMMAND : %s', command)
    process = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               cwd=cwd)

    if not wait:
        return None

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
