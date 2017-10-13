"""Unit tests of `eve.setup.www_dashboards`."""

from __future__ import absolute_import

from io import StringIO

import yaml
from mock import patch
from twisted.trial import unittest

from eve.setup.www_dashboards import (DashboardsConfig, metabase_dashboard,
                                      wsgi_dashboards)

correct_data = [
    {
        'type': 'metabase',
        'name': 'monitoring_1',
        'caption': 'Monitoring',
        'site_url': 'http://metabase.org',
        'secret_key': 'secret',
        'id': '100',
        'icon': 'test-icon',
        'order': '10',
        'frameborder': '10',
        'width': '10%',
        'height': '100',
    },
    {
        'type': 'metabase',
        'name': 'monitoring_2',
        'caption': 'Monitoring 2',
        'site_url': 'http://metabase.org',
        'secret_key': 'secret 2',
        'id': '1',
    },
    {
        'name': 'no_type',
    },
]


class TestDashboardsConfig(unittest.TestCase):
    @patch('eve.setup.www_dashboards.open')
    def test_dashboards_invalid_yaml(self, mock_open):
        mock_open.return_value = StringIO(u"not: 'yaml")
        with self.assertRaises(yaml.YAMLError):
            DashboardsConfig('mock')

    @patch('eve.setup.www_dashboards.open')
    def test_dashboards_not_a_list(self, mock_open):
        mock_open.return_value = StringIO(u"not: a list")
        with self.assertRaises(TypeError):
            DashboardsConfig('mock')

    @patch('eve.setup.www_dashboards.open')
    def test_dashboards_correct_yaml(self, mock_open):
        data = yaml.dump(correct_data).decode('utf-8')
        mock_open.return_value = StringIO(data)
        conf = DashboardsConfig('mock').iter()

        dashboard = conf.next()
        self.assertEqual(dashboard, {
            'type': 'metabase',
            'name': 'monitoring_1',
            'caption': 'Monitoring',
            'site_url': 'http://metabase.org',
            'secret_key': 'secret',
            'id': '100',
            'icon': 'test-icon',
            'order': '10',
            'frameborder': '10',
            'width': '10%',
            'height': '100',
        })

        dashboard = conf.next()
        self.assertEqual(dashboard, {
            'type': 'metabase',
            'name': 'monitoring_2',
            'caption': 'Monitoring 2',
            'site_url': 'http://metabase.org',
            'secret_key': 'secret 2',
            'id': '1',
        })

        dashboard = conf.next()
        self.assertEqual(dashboard, {
            'type': 'unknown',
            'name': 'no_type',
        })


class TestWsgiDashboards(unittest.TestCase):
    def mock_env():
        return {
            'DASHBOARDS_FILE_PATH': 'a_filename'
        }

    @patch('eve.setup.www_dashboards.util.env')
    @patch('eve.setup.www_dashboards.metabase_dashboard')
    @patch('eve.setup.www_dashboards.open')
    def test_wsgi_dashboards(self,
                             mock_open,
                             mock_metabase_dashboard,
                             mock_env):
        mock_env.request.side_effect = self.mock_env
        mock_metabase_dashboard.return_value = {
            'name': 'mock_name',
            'caption': 'mock_caption',
            'app': 'mock_app',
            'order': 'mock_order',
            'icon': 'mock_icon',
        }
        data = yaml.dump(correct_data).decode('utf-8')
        mock_open.return_value = StringIO(data)

        ret = wsgi_dashboards()

        self.assertEqual(ret, [
            {
                'caption': 'mock_caption',
                'order': 'mock_order',
                'app': 'mock_app',
                'name': 'mock_name',
                'icon': 'mock_icon'
            }, {
                'caption': 'mock_caption',
                'order': 'mock_order',
                'app': 'mock_app',
                'name': 'mock_name',
                'icon': 'mock_icon'
            }])


class TestMetabaseDashboard(unittest.TestCase):
    def test_metabase_dashboard(self):
        ret = metabase_dashboard(correct_data[0])
        self.assertEqual(ret['name'], 'monitoring_1')
        self.assertEqual(ret['caption'], 'Monitoring')
        self.assertEqual(ret['order'], 10)
        self.assertEqual(ret['icon'], 'test-icon')

        ret = metabase_dashboard(correct_data[1])
        self.assertEqual(ret['name'], 'monitoring_2')
        self.assertEqual(ret['caption'], 'Monitoring 2')
        self.assertEqual(ret['order'], 50)
        self.assertEqual(ret['icon'], 'bar-chart')

        self.assertIsNone(metabase_dashboard(correct_data[2]))
