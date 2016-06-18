import unittest
import subprocess
from subprocess import check_output as cmd


def run_buildbot():
    try:
        cmd(['buildbot', 'stop', 'master'])
    except subprocess.CalledProcessError:
        pass
    cmd(['buildbot', 'create-master', 'master'])
    cmd(['cp', 'buildbot/master.cfg.py', 'master/master.cfg'])
    # cmd(['cp', 'master/master.cfg.sample', 'master/master.cfg'])
    execfile('master/master.cfg')
    try:
        cmd(['buildbot', 'start', 'master'])
        return True
    except subprocess.CalledProcessError as e:
        with open('master/twistd.log') as logfile:
            print(logfile.read())
        print "Ping stdout output:\n", e.output
        raise


class TestEnd2End(unittest.TestCase):
    def setUp(self):
        run_buildbot()

    def test_run(self):
        pass
