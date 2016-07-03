import os
import time
from argparse import ArgumentParser

import requests

from deploy.buildbot_api_client import BuildbotDataAPi
from deploy.docker_api_client import Docker


class EveMaster:
    def __init__(self,
                 bitbucket_git_repo,
                 bitbucket_git_cert_key_baser64,
                 master_fqdn,
                 eve_bitbucket_login,
                 eve_bitbucket_pwd,
                 eve_web_login,
                 eve_web_pwd,
                 worker_docker_host,
                 worker_docker_cert_path,
                 worker_docker_use_tls):
        self.worker_docker_cert_path = worker_docker_cert_path
        self.eve_env_vars = {
            'GIT_REPO': bitbucket_git_repo,
            'EVE_BITBUCKET_LOGIN': eve_bitbucket_login,
            'EVE_BITBUCKET_PWD': eve_bitbucket_pwd,
            'EVE_WEB_LOGIN': eve_web_login,
            'EVE_WEB_PWD': eve_web_pwd,
            'DOCKER_HOST': worker_docker_host,
            'DOCKER_USE_TLS': worker_docker_use_tls,
            'MASTER_FQDN': master_fqdn,
            'GIT_CERT_KEY_BASE64': bitbucket_git_cert_key_baser64,
        }

        api_base_url = 'http://%s:8000/api/v2/' % master_fqdn
        self.api = BuildbotDataAPi(api_base_url)

    def deploy(self,
               master_docker_host,
               master_docker_cert_path,
               master_docker_use_tls):
        self.docker = Docker(
            'eve',
            docker_host=master_docker_host,
            docker_cert_path=master_docker_cert_path,
            docker_use_tls=master_docker_use_tls)
        self.docker.build_image(worker_cert_path=self.worker_docker_cert_path)
        self.docker.rm_all(force=True)
        self.docker.run('eve', env_vars=self.eve_env_vars)

    def wait(self):

        for i in range(10):
            try:
                print('checking buildbot\'s webserver response')
                builds = self.api.get('builds')
                assert builds['meta']['total'] == 0
                break
            except requests.ConnectionError:
                time.sleep(1)
            else:
                raise Exception('Could not connect to API')


def main():
    parser = ArgumentParser(description='Deploy am EVE master.')

    parser.add_argument(
        'git_repo',
        help='The git repo. e.g., git@example.org:repo.git')

    parser.add_argument(
        'fqdn',
        help='The fully qualified domain name to be used for the web URL'
             '. e.g., example.com')

    args = parser.parse_args()

    if not args.fqdn:
        docker_host = os.environ['DOCKER_HOST']
        args.fqdn = docker_host.replace('tcp://', '').split(':')[0]

    eve = EveMaster(
        bitbucket_git_repo=args.git_repo,
        master_fqdn=args.fqdn,
        eve_bitbucket_login=os.environ['EVE_BITBUCKET_LOGIN'],
        eve_bitbucket_pwd=os.environ['EVE_BITBUCKET_PWD'],
        worker_docker_host=os.environ['DOCKER_HOST'],
        worker_docker_cert_path=os.environ['DOCKER_CERT_PATH'],
        worker_docker_use_tls=os.environ['DOCKER_TLS_VERIFY'],
    )
    eve.deploy(
        master_docker_host=os.environ['DOCKER_HOST'],
        master_docker_cert_path=os.environ['DOCKER_CERT_PATH'],
        master_docker_use_tls=os.environ['DOCKER_TLS_VERIFY'],
    )
    eve.wait()


if __name__ == '__main__':
    main()
