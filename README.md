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

Configure the following environment variables (can be added to the virtual
env postactivate script for example); important items are marked with a *

    #!/bin/bash
    export EXTERNAL_URL=http://localhost:8999/
    export MASTER_DOCKER_NAME=eve_dev  # (*) customize with username for
                                       #  example
    export MASTER_NAME=eve1 # Name of this master instance. This will be used as
                            # a name prefix to differenciate schedulers,
                            # masters, and workers in a multi-master setup
    export EVE_GITHOST_LOGIN=test
    export EVE_GITHOST_PWD=test
    export OAUTH2_CLIENT_ID=test
    export OAUTH2_CLIENT_SECRET=test
    export PROJECT_NAME=dev  # (*) customize with username for example
    export PROJECT_URL=foo
    export TRY_PWD=foo
    export TRY_PORT=7999
    export HTTP_PORT=8999  # (*) change port to desired value
    export PB_PORT=9999
    export HIPCHAT_TOKEN=fake
    export HIPCHAT_ROOM=fake
    export MASTER_FQDN=172.17.0.1  # (*) should work on most installations
    export WORKER_SUFFIX=dev_eve  # (*) customize with username for example
    export GIT_REPO=$HOME/project_source  # (*) local path to project to build
    export NGROK=/usr/local/ngrok # path to ngrok if installed, usefull if you
                                  # need to spawn distant VMs (ex. OS worker)
    unset DB_URL  # (*) pass a mysql DB URL if needed, will use sqlite if unset
    unset DOCKER_HOST  # set to URI to be used; will use local Docker if left
                       # empty
    unset DOCKER_TLS_VERIFY  # required if remote unix socket is used (e.g.
                             # Carina)
    unset DOCKER_CERT_PATH  # same
    unset DOCKER_VERSION  # used by older versions of client (?)
    unset RAX_LOGIN  # required to run tests with openstack slaves (tests are
                     # skipped if left empty)
    unset RAX_PWD  # same (rackspace password, not API_KEY)
    unset OPENSTACK_SSH_KEY  # same, defaults to ~/.ssh/id_rsa
    unset OPENSTACK_KEY_NAME  # same, defaults to eve-key-pair
    unset CLOUD_INIT_SCRIPT # path to script to execute on vm workers init


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
- you need to define a key named as OPENSTACK_KEY_NAME in openstack identities
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

You can tailor the way tests are run by setting the following env variables:

    DOCKER_HOST
    DOCKER_TLS_VERIFY
    DOCKER_CERT_PATH
    DOCKER_VERSION
    RAX_LOGIN
    RAX_PWD
    OPENSTACK_SSH_KEY

Run tests with:

    $ tox -e test
