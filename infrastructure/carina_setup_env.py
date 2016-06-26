import os
import sys
from subprocess import check_output

assert os.environ['CARINA_USERNAME']
assert os.environ['CARINA_APIKEY']
CARINA_BIN_URL = 'https://download.getcarina.com/carina/latest/' \
                 '$(uname -s)/$(uname -m)/carina -o carina'


def generate_carina_environment(carina_cluster):
    if not os.path.isfile('carina'):
        check_output('curl -L %s' % CARINA_BIN_URL, shell=True)
        check_output('chmod u+x ./carina', shell=True)

    if carina_cluster not in check_output('./carina ls', shell=True):
        check_output('./carina create --wait %s' % carina_cluster, shell=True)
    return check_output('./carina env %s' % carina_cluster, shell=True)

if __name__ == '__main__':
    # get the cluster name from args and print the env variables required by
    # docker to stdout. Use eval $(python carina_setup_env.py <cluster_name>)
    # to export these env vars to you shell
    carina_cluster_name = sys.argv[1]
    print(generate_carina_environment(carina_cluster_name))
