#!/usr/bin/env python3.6

import argparse
# from jira import JIRA
import logging
# import sys
import os
import time

from eve_client import EveClient
from githost import getProvider, guessProvider
from utils import EnvDefault

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


def collect_step_artifacts(tree, stepname, collect=False):
    if (not stepname
            or ('step' in tree and tree['step'] == stepname)
            or ('stage' in tree and tree['stage'] == stepname)):
        collect = True

    artifacts = []
    if collect is True:
        artifacts += tree['artifacts']
    for url, build in tree['builds'].items():
        artifacts += collect_step_artifacts(build, stepname, collect)
    return artifacts


def extract_name(url, dir_parts=0):
    name = os.path.basename(url)
    dir = os.path.dirname(url)
    for i in range(dir_parts):
        name = os.path.basename(dir) + '_' + name
        dir = os.path.dirname(dir)
    return name


def sanitize_names(urls):
    """ Transform a set of urls into a set of the smallest names possible
        extracted from the urls.

        If two names match, then all of them are prepended with one additional
        parent folder name from the URL.
    """
    sanitized_names = []
    dir_parts = 0
    while len(set(sanitized_names)) != len(urls):
        sanitized_names = [extract_name(url, dir_parts) for url in urls]
        dir_parts += 1
    return sanitized_names


if __name__ == '__main__':

    parser = argparse.ArgumentParser('Download NW failure artifacts and '
                                     'reattach them to the relevant issue')
    parser.add_argument('--auth-client', '-u',
                        help='Consumer client id (if applicable). '
                             'Can also be set with environment variable '
                             'EVE_API_CLIENT_ID.',
                        action=EnvDefault, envvar='EVE_API_CLIENT_ID')
    parser.add_argument('--auth-secret', '-p',
                        help='Consumer client secret (if applicable). '
                             'Can also be set with environment variable '
                             'EVE_API_CLIENT_SECRET.',
                        action=EnvDefault, envvar='EVE_API_CLIENT_SECRET')
    parser.add_argument('--auth-token', '-t',
                        help='Git host authentication token. '
                             'Can also be set with environment variable '
                             'EVE_API_TOKEN.',
                        action=EnvDefault, envvar='EVE_API_TOKEN',
                        default='')
    parser.add_argument('--base-url', '-b',
                        help='Eve base url. '
                             'Can also be set with environment variable '
                             'EVE_API_HOST.',
                        action=EnvDefault, envvar='EVE_API_HOST',
                        default='https://eve.devsca.com')
    parser.add_argument('--api-version', '-v',
                        help='API version to use (defaults to v2). '
                             'Can also be set with environment variable '
                             'EVE_API_VERSION.',
                        action=EnvDefault, envvar='EVE_API_VERSION',
                        metavar='INT', type=int,
                        default=2)
    parser.add_argument('--jira-user', '-U',
                        help='JIRA User. '
                             'Can also be set with environment variable '
                             'JIRA_USERNAME.',
                        action=EnvDefault, envvar='JIRA_USERNAME')
    parser.add_argument('--jira-pass', '-P',
                        help='JIRA Password. '
                             'Can also be set with environment variable '
                             'JIRA_PASSWORD.',
                        action=EnvDefault, envvar='JIRA_PASSWORD')
    parser.add_argument('--step-name', '-s',
                        help='Name of the step/stage to collect '
                             'the artifacts for. Artifacts of all builds or '
                             'steps triggered by this step will be collected.',
                        default=None)
    parser.add_argument('eve_project', help='Eve project name')
    parser.add_argument('build_id', help='Eve bootstrap build number')
    parser.add_argument('jira_issue', help='Jira issue ID')
    args = parser.parse_args()

    jira = {
        'user': args.jira_user,
        'password': args.jira_pass,
        'issue': args.jira_issue,
    }
    authparams = {
        'client_id': args.auth_client,
        'client_secret': args.auth_secret,
        'token': args.auth_token,
    }
    build = {
        'url': '{}/{}'.format(args.base_url, args.eve_project),
        'project': args.eve_project,
        'id': args.build_id,
    }

    githost = guessProvider('auto', None, build['project'])
    provider = getProvider(githost, **authparams)
    eve = EveClient(provider.token, build['url'])
    print('Building tree of builds and artifacts...')
    start_building = time.time()
    buildtree = eve.buildtree('bootstrap', build['id'])
    end_building = time.time()
    spent_building = end_building - start_building
    logging.debug('Spend {}s retrieving the build tree'.format(spent_building))

    artifacts = collect_step_artifacts(buildtree, args.step_name)
    logging.info('Collecting artifacts:')
    for artifact in artifacts:
        logging.info(' - {}'.format(artifact))

    # Ensure that no two basenames are identical
    sanitized_names = sanitize_names(artifacts)
    for fname, url in zip(sanitized_names, artifacts):
        logging.info('Generating attachment "{}"\n\t-> "{}"'
                     .format(fname, url))
