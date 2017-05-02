"""This test suite checks end-to-end ec2 operation of EVE."""
import unittest

from tests.util.cluster import Cluster
from tests.util.yaml_factory import SingleCommandYaml

class TestEC2(unittest.TestCase):

    def test_ec2(self):
        """Tests that the build fails when the YAML file is empty
        """
        import os
        os.environ['AWS_ACCESS_KEY_ID'] = '<PUT YOUR CREDS HERE>'
        os.environ['AWS_SECRET_ACCESS_KEY'] = '<PUT YOUR CREDS HERE>'
        os.environ['AWS_SSH_KEY'] = 'eve'
        os.environ['AWS_REGION_NAME'] = 'us-east-1'

        cluster = Cluster().start()
        print cluster.api.url
        local_repo = cluster.clone()



        local_repo.push(yaml=SingleCommandYaml('exit 0', worker={
            'type': 'ec2',
            'ami': 'ami-80861296',
            'instance_type': 't2.micro',
        }))
        buildset = cluster.force(local_repo.branch)
        assert buildset.result == 'success'

