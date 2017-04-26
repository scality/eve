# Eve

Pipeline as code in Buildbot

## Support

Please open an issue on JIRA RELENG project for support.

## Contributing

Please contribute using the ticketing process. Create a branch, add commits,
and open a pull request.

## Developper environment
Install the libraries required for mysql on your machine:

    # ubuntu:
    $ sudo apt-get install libmysqlclient-dev

    # or CentOS:
    $ yum install mysql-devel

Next install eve requirements (virtual env recommended):

    $ pip install -r requirements/base.txt

Configure the environment variables required by master.cfg. (can be added to the virtual
env postactivate script for example); Eve will not start if a value is missing.

Create and start buildbot:

    buildbot create-master eve
    buildbot start eve

Next, configure the branches you want to build automatically. The selection of
branches is done in the yaml file of the project. Since we are working locally,
with no hook targetting Eve when the repository is updated, you can increase
the poll interval on the repositoryt in master.cfg:

    pollinterval=10

When doing changes to the configuration, you can restart buildbot with:

    buildbot restart eve

To follow activity of buildbot:

    tail -f eve/twistd.log


Notes for developpers intending to use Openstack slaves:

- slaves will try to contact the master, and therefore a public IP is required
- you need to define a key named as OS_KEY_NAME in openstack identities
  (directly in rackspace interface, or via nova with the command below)



```
#!bash

    $ nova --os-username "YOUR_USERNAME" --os-project-name test \
      --os-auth-url "https://identity.api.rackspacecloud.com/v2.0/" \
      --os-tenant-id "YOUR_TENANT_ID" --os-region-name "YOUR_REGION" \
      --os-password 'YOUR_PASSWORD' keypair-add --pub-key ~/.ssh/id_rsa.pub \
      $OPENSTACK_KEY_NAME
```



## How to run tests
The installation of mysql dev environment and tox are required.

You can tailor the way tests are run by setting some environment variables,
listed in tox.ini, `passenv` section. The other variables are hardcoded
for the tests.

Run tests with:

    $ tox -e unit
    $ tox -e testutil
    $ tox -e system
    $ tox -e docker
    $ tox -e autoformatcheck

To investigate a failure for a specific test case:

    $ tox -e system -- -k test_name --pdb

    # at debugger prompt, find out eve url with:
    (pdb) print cluster.api.url
    http://localhost:52909/

    # find the name of the buildbot instances:
    (pdb) print cluster._masters.keys
    ['frontend52909', 'backend44190']

    # logs are stored in /tmp:
    cat /tmp/1493216925.55RDRKM__eve_frontend52909/twistd.log
