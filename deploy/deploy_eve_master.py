# coding: utf-8
"""Deploy an EVE instance."""
import logging
import os
import time
from argparse import ArgumentParser
from urlparse import urlparse, urljoin

import requests

from deploy.buildbot_api_client import BuildbotDataAPI
from deploy.docker_api_client import Docker

logger = logging.getLogger(__name__)
logging.getLogger('requests').setLevel(logging.WARNING)

MAX_EVE_API_TRIES = 10


class EveMaster(object):
    """Gathers all the parameters and deploys an EVE instance."""

    def __init__(self,
                 git_repo_name,
                 external_url,
                 project_name,
                 project_url):
        name = 'eve__%s' % git_repo_name.replace('/', '-')
        bitbucket_git_repo = \
            'git@bitbucket.org:%s.git' % git_repo_name
        self.name = name
        self.external_url = external_url
        api_base_url = urljoin(self.external_url, 'api/v2/')

        self.eve_env_vars = {
            'GIT_REPO': bitbucket_git_repo,
            'EXTERNAL_URL': self.external_url,
            'MASTER_DOCKER_NAME': name,
            'PROJECT_NAME': project_name,
            'PROJECT_URL': project_url,
        }
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

    def deploy(self, master_docker_host, master_docker_cert_path,
               workers_docker_host, workers_docker_cert_path,
               http_port, pb_port):
        """Deploy an EVE instance on docker."""

        self.eve_env_vars['DOCKER_HOST'] = workers_docker_host
        logger.info('=> Creating docker image <%s> on %s...',
                    self.name, master_docker_host)
        self.docker = Docker(
            self.name,
            docker_host=master_docker_host,
            docker_cert_path=master_docker_cert_path)
        self.docker.build_image(
            name=self.name,
            git_cert_path='certs/git',
            master_docker_cert_path=master_docker_cert_path,
            workers_docker_cert_path=workers_docker_cert_path,
        )
        logger.info('=> Removing docker instance of <%s> if it exists',
                    self.name)
        self.docker.rm_all(self.name, force=True)
        logger.info('=> Creating a new instance of <%s>', self.name)
        container_id = self.docker.run(
            self.name, env_vars=self.eve_env_vars, http_port=http_port,
            pb_port=pb_port)

        return container_id

    def wait(self, container_id):
        """Polls the REST API of an EVE instance until it responds."""
        time.sleep(5)
        for i in range(MAX_EVE_API_TRIES):
            try:
                logger.info('=> Checking response from %s (retry %d/%d)',
                            self.external_url,
                            i + 1,
                            MAX_EVE_API_TRIES)
                builds = self.api.get('builds')
                assert builds['meta']['total'] == 0
                return
            except requests.ConnectionError:
                time.sleep(1)
        logger.error(self.docker.client.logs(container_id))
        raise Exception('Could not connect to API')


def main():
    """Allows to spwan EVE from the command line."""
    parser = ArgumentParser(description='Deploy an EVE master.')
    parser.add_argument(
        'git_repo_name',
        help='The git repo full name. e.g., scality/wall-e, scality/ring')
    parser.add_argument(
        '--master_docker_host',
        default=os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock'),
        help='The url of the docker host that will host the eve master '
             'container. Default value is $DOCKER_HOST if defined or '
             'unix:///var/run/docker.sock otherwise. If a unix socket is used,'
             ' --master_docker_cert_path is ignored')
    parser.add_argument(
        '--master_docker_cert_path',
        default=os.environ.get('DOCKER_CERT_PATH', 'certs/docker_master'),
        help='The path to the master docker host\'s certificates. Default '
             'value is $DOCKER_CERT_PATH if defined or certs/docker_master '
             'otherwise')
    parser.add_argument(
        '--workers_docker_host',
        default=os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock'),
        help='The url of the workers\' docker host. Default value '
             'is $DOCKER_HOST if defined or '
             'unix:///var/run/docker.sock otherwise If a unix socket is used, '
             '--workers_docker_cert_path is ignored')
    parser.add_argument(
        '--workers_docker_cert_path',
        default=os.environ.get('DOCKER_CERT_PATH', 'certs/docker_master'),
        help='The path to the docker host\'s certificates. Default value is '
             '$DOCKER_CERT_PATH if defined or certs/docker_master otherwise')
    parser.add_argument(
        '--public_web_url',
        default=None,
        help='The URL of the web server as seen by the end users (E.g., the '
             'URL of a reverse proxy. If omitted, a default value will be '
             'extracted from --master_docker_host and --http_port')
    parser.add_argument(
        '--http_port',
        default=8000,
        type=int,
        help='The port on which the buildbot will listen for HTTP requests '
             'on the master docker host')
    parser.add_argument(
        '--pb_port',
        default=9000,
        type=int,
        help='The port on which the buildbot will listen for its workers on '
             'the master docker host')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase verbosity (may be supplied two times)')
    args = parser.parse_args()

    if urlparse(args.master_docker_host).scheme == 'unix':
        args.master_docker_cert_path = None
        args.public_web_url = 'http://localhost:%d/' % args.http_port

    if urlparse(args.workers_docker_host).scheme == 'unix':
        args.workers_docker_cert_path = None

    if args.public_web_url is None:
        fqdn = urlparse(args.master_docker_host).hostname
        args.public_web_url = 'http://%s:%d/' % (fqdn, args.http_port)

    # Set up basic logging according to selected verbosity
    logging.basicConfig(
        format='%(message)s',
        level={
            0: logging.WARNING,
            1: logging.INFO,
            2: logging.DEBUG,
        }[args.verbose],
    )
    eve = EveMaster(
        args.git_repo_name,
        external_url=args.public_web_url,
        project_name=args.git_repo_name,
        project_url='https://bitbucket.org/%s/' % args.git_repo_name
    )
    eve.set_bitbucket_credentials(
        os.environ['EVE_BITBUCKET_LOGIN'],
        os.environ['EVE_BITBUCKET_PWD'])
    eve.set_web_credentials(
        os.environ['EVE_WEB_LOGIN'],
        os.environ['EVE_WEB_PWD'])
    container_id = eve.deploy(
        master_docker_host=args.master_docker_host,
        master_docker_cert_path=args.master_docker_cert_path,
        workers_docker_host=args.workers_docker_host,
        workers_docker_cert_path=args.workers_docker_cert_path,
        http_port=args.http_port, pb_port=args.pb_port)
    eve.wait(container_id)
    return eve

if __name__ == '__main__':
    main()
