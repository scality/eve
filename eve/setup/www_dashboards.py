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
"""Extra dashboards."""

import jwt
import yaml
from buildbot.plugins import util
from flask import Flask
from twisted.logger import Logger

logger = Logger('eve.setup.www_dashboard')


class DashboardsConfig(object):
    """Parse a dashboard config file."""

    def __init__(self, conf_path):
        try:
            with open(conf_path) as dash_file:
                self.config = yaml.load(dash_file.read())
        except (OSError, IOError, yaml.YAMLError) as err:
            logger.error(
                'An error occured while loading the dashboard config file at '
                '{path}: {err}', path=conf_path, err=err)
            raise

        if not isinstance(self.config, list):
            raise TypeError(
                'Dashboard config file is not a list: '
                '{conf}'.format(conf=self.config))
        logger.info("Dashboards config: {conf}", conf=self.config)

    def iter(self):
        """Yield configurations."""
        for data in self.config:
            # garanty at least a 'type' key
            full_data = dict(data)
            full_data.setdefault('type', 'unknown')
            yield full_data


def link_dashboard(conf):
    """Return a Buildbot WSGI dashboard.

    This method creates a Flask application serving a dashboard inside
    a buildbot dashboard.

    Args:
      conf (dict): configuration of dashboard to serve,
        with the following keys:
        - caption: label of dashboard in buildbot menu
        - id: unique identifier of the dashboard to serve
        - name: unique identifier of the buildbot dashboard
        - site_url: address of service instance
        - order (optional): order of dashboard in buildbot menu
        - icon (optional): icon to display next to label in buildbot menu
        - frameborder (optional): border of iframe in buildbot interface
        - width (optional): width of iframe in buildbot interface
        - height (optional): height of iframe in buildbot interface

    Return:
        dict: a buildbot WSGI dashboard, or None in case of parsing error

    """
    try:
        caption = conf['caption']
        dashboard_id = int(conf['id'])
        name = conf['name']
        site_url = conf['site_url']
        order = int(conf.get('order', 50))
    except (KeyError, ValueError):
        return

    app = Flask('name')

    @app.route("/index.html")
    def index():
        border = conf.get('frameborder', "0")
        url = None

        if conf['type'] == 'metabase':
            payload = {
                "resource": {"dashboard": dashboard_id},
                "params": {}
            }
            token = jwt.encode(payload, conf['secret_key'], algorithm="HS256")

            url = '{site_url}/embed/dashboard/{token}' \
                  '#bordered={bordered}&titled=false'.format(
                      site_url=site_url,
                      token=token.decode('utf-8'),
                      bordered='true' if border else 'false')
        else:
            url = '{site_url}' \
                  '#bordered={bordered}&titled=false'.format(
                      site_url=site_url,
                      bordered='true' if border else 'false')

        return '<iframe src="{url}" frameborder="{border}" ' \
               'width="{width}" height="{height}" ' \
               'allowtransparency></iframe>'.format(
                   url=url,
                   border=border,
                   width=conf.get('width', "100%"),
                   height=conf.get('height', "1200"))

    return {
        'name': name,
        'caption': caption,
        'app': app,
        'order': order,
        'icon': conf.get('icon', 'bar-chart')
    }


def wsgi_dashboards():
    if not util.env['DASHBOARDS_FILE_PATH']:
        return []

    dashboards = []
    config = DashboardsConfig(util.env['DASHBOARDS_FILE_PATH'])

    for conf in config.iter():
        if conf['type'] in ('standard', 'metabase'):
            dashboard = link_dashboard(conf)
        else:
            logger.error(
                'Unknown dashboard type while loading dashboards '
                '{conf}', conf=conf)
            continue

        if not dashboard:
            logger.error(
                'Could not load dashboard: {conf}', conf=conf)
            continue

        logger.info(
            'Adding a dashboard of type {type}', type=conf['type'])
        dashboards.append(dashboard)

    return dashboards
