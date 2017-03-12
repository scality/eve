import datetime
from os import environ

import buildbot.www.authz.endpointmatchers as bb_endpointmatchers
from buildbot.www.auth import UserPasswordAuth
from buildbot.www.authz import Authz
from buildbot.www.hooks import bitbucket
from buildbot.www.oauth2 import GoogleAuth

import authz.endpointmatchers as eve_endpointmatchers
import authz.roles as eve_roles
import webhooks.bitbucket


def setup_www(conf, bootstrap_builder_name):
    #########################################
    # HACK: Replace default bitbucket webhook
    #########################################

    bitbucket.getChanges = webhooks.bitbucket.getChanges

    ###########################
    # Web UI
    ###########################
    oauth2_client_id = environ.pop('OAUTH2_CLIENT_ID', None)
    oauth2_client_secret = environ.pop('OAUTH2_CLIENT_SECRET', None)

    conf['www'] = {
        'port': environ['HTTP_PORT'],
        'plugins': {},
        'change_hook_dialects': {
            'bitbucket': True,
            'github': {}
        },
        'debug': True,
        'cookie_expiration_time': datetime.timedelta(weeks=1),
    }

    if oauth2_client_id and oauth2_client_secret:
        conf['www']['auth'] = GoogleAuth(
            oauth2_client_id, oauth2_client_secret
        )
    else:
        conf['www']['auth'] = UserPasswordAuth({'eve': 'eve'})

    conf['www']['authz'] = Authz(
        allowRules=[
            eve_endpointmatchers.DenyRebuildIntermediateBuild(
                bootstrap_builder_name,
                role='developer'  # This parameter is not necessary,
                                  #   the next rule will deny access.
            ),
            bb_endpointmatchers.AnyEndpointMatcher(role='developer'),
        ],
        roleMatchers=[
            eve_roles.DeveloperRoleIfConnected()
        ]
    )
