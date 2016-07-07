#coding: utf-8
"""Deploy an EVE instance."""
from argparse import ArgumentParser
import logging
import os
import time

import requests

from deploy.buildbot_api_client import BuildbotDataAPI
from deploy.docker_api_client import Docker

logger = logging.getLogger(__name__)
logging.getLogger('requests').setLevel(logging.WARNING)

MAX_EVE_API_TRIES = 10


class EveMaster(object):
    """Gathers all the parameters and deploys an EVE instance."""

    def __init__(self,
                 bitbucket_git_repo,
                 bitbucket_git_cert_key_baser64,
                 master_fqdn,
                 worker_docker_host,
                 project_name,
                 project_url):
        self.eve_env_vars = {
            'GIT_REPO': bitbucket_git_repo,
            'DOCKER_HOST': worker_docker_host,
            'MASTER_FQDN': master_fqdn,
            'GIT_CERT_KEY_BASE64': bitbucket_git_cert_key_baser64,
            'PROJECT_NAME': project_name,
            'PROJECT_URL': project_url,
        }

        api_base_url = 'https://%s/api/v2/' % master_fqdn
        self.api = BuildbotDataAPI(api_base_url)
        self.docker = None

    def set_bitbucket_credentials(
            self,
            eve_bitbucket_login,
            eve_bitbucket_pwd):
        """Sets bitbucket credentials to be used by EVE."""
        self.eve_env_vars['EVE_BITBUCKET_LOGIN'] = eve_bitbucket_login
        self.eve_env_vars['EVE_BITBUCKET_PWD'] = eve_bitbucket_pwd

    def set_web_credentials(
            self,
            eve_web_login,
            eve_web_pwd):
        """Sets credentials that will allow to connect to the Web/API."""
        self.eve_env_vars['EVE_WEB_LOGIN'] = eve_web_login
        self.eve_env_vars['EVE_WEB_PWD'] = eve_web_pwd
        self.api.add_auth(eve_web_login, eve_web_pwd)

    def deploy(self,
               master_docker_host,
               master_docker_cert_path,
               worker_docker_cert_path):
        """Deploy an EVE instance on docker."""
        self.docker = Docker(
            'eve',
            fqdn=self.eve_env_vars['MASTER_FQDN'],
            login=self.eve_env_vars['EVE_WEB_LOGIN'],
            pwd=self.eve_env_vars['EVE_WEB_PWD'],
            docker_host=master_docker_host,
            docker_cert_path=master_docker_cert_path)
        self.docker.build_image(worker_cert_path=worker_docker_cert_path)
        self.docker.rm_all(force=True)
        self.docker.run('eve', env_vars=self.eve_env_vars)

    def wait(self):
        """Polls the REST API of an EVE instance until it responds."""

        for i in range(MAX_EVE_API_TRIES):
            try:
                logger.info('Checking buildbot\'s webserver response (retry %d/%d)',
                            i + 1, MAX_EVE_API_TRIES)
                builds = self.api.get('builds')
                assert builds['meta']['total'] == 0
                return
            except requests.ConnectionError:
                time.sleep(1)
        raise Exception('Could not connect to API')


def main():
    """Allows to spwan EVE from the command line."""
    parser = ArgumentParser(description='Deploy an EVE master.')
    parser.add_argument('git_repo',
                        help='The git repo. e.g., git@example.org:repo.git')
    parser.add_argument('fqdn',
                        help='The fully qualified domain name to be used for '
                             'the web URL (e.g. example.com)')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase verbosity (may be supplied two times)')
    args = parser.parse_args()

    # Set up basic logging according to selected verbosity
    logging.basicConfig(
        format='%(message)s',
        level={
            0: logging.WARNING,
            1: logging.INFO,
            2: logging.DEBUG,
        }[args.verbose],
    )

    if not args.fqdn:
        docker_host = os.environ['DOCKER_HOST']
        args.fqdn = docker_host.replace('tcp://', '').split(':')[0]

    eve = EveMaster(
        bitbucket_git_repo=args.git_repo,
        bitbucket_git_cert_key_baser64=os.environ['GIT_CERT_KEY_BASE64'],
        master_fqdn=args.fqdn,
        worker_docker_host=os.environ['DOCKER_HOST'],
        project_name=os.environ['PROJECT_NAME'],
        project_url=os.environ['PROJECT_URL'],
    )
    eve.set_bitbucket_credentials(
        os.environ['EVE_BITBUCKET_LOGIN'],
        os.environ['EVE_BITBUCKET_PWD'])
    eve.set_web_credentials(
        os.environ['EVE_WEB_LOGIN'],
        os.environ['EVE_WEB_PWD'])
    eve.deploy(
        master_docker_host=os.environ['DOCKER_HOST'],
        master_docker_cert_path=os.environ['DOCKER_CERT_PATH'],
        worker_docker_cert_path=os.environ['DOCKER_CERT_PATH'],
    )
    eve.wait()


if __name__ == '__main__':
    main()
