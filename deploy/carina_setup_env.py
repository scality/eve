#coding: utf-8
"""Generate CARINA environment variables required by docker clients."""
from __future__ import print_function

import os
from subprocess import check_output
import sys

assert os.environ['CARINA_USERNAME']
assert os.environ['CARINA_APIKEY']
CARINA_BIN_URL = 'https://download.getcarina.com/carina/latest/' \
                 '$(uname -s)/$(uname -m)/carina'


def generate_carina_environment(carina_cluster):
    """Generate CARINA environment variables.

    It uses the cluster name and the CARINA credentials.
    """
    if not os.path.isfile('carina'):
        check_output('curl -L %s  -o carina' % CARINA_BIN_URL, shell=True)
        check_output('chmod u+x ./carina', shell=True)

    if carina_cluster not in check_output('./carina ls', shell=True):
        check_output('./carina create --wait %s' % carina_cluster, shell=True)
    return check_output('./carina env %s' % carina_cluster, shell=True)

if __name__ == '__main__':
    # get the cluster name from args and print the env variables required by
    # docker to stdout. Use eval $(python carina_setup_env.py <cluster_name>)
    # to export these env vars to you shell
    CARINA_CLUSTER_NAME = sys.argv[1]
    print(generate_carina_environment(CARINA_CLUSTER_NAME))
