API client
==========

Eve is shipped with a python client that can be used to access most of the
resources in Buildbot from the command line.

The script can be found in `Eve repository`_, in the tools directory.

The client is currently compatible with the following authentication
methods:

- Bitbucket OAuth
- Github OAuth

Check the script itself for details on how to setup authentication tokens
for the various OAuth providers, and examples on how to run the script.

.. _Eve repository: https://bitbucket.org/scality/eve/

Force build helper
------------------

Using the API client, it is possible to launch builds from the command line.
Simply put a copy of eve_api_client into the path, and create the following
script ``build``:

.. code-block:: shell

    #!/bin/bash
    set -u

    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    PAYLOAD="{\"branch\":\"$BRANCH\"}"

    reply=$(eve_api_client --username "${USER}" \
                           --password "${PASS}" \
                           --consumer-key "${KEY}" \
                           --base-url "${EVE_URL}" \
                           --httpmethod post \
                           --payload "${PAYLOAD}" \
                           /forceschedulers/force)

    # reply format is json:
    # {"id": 999, "jsonrpc": "2.0", "result": [345, {"2": 345}]}
    BUILDREQUEST=$(echo "${reply}" | jq -r '.result[0]')

    echo "${EVE_URL}/#/buildrequests/${BUILDREQUEST}?redirect_to_build=true"

Call this script from the repository and branch you would like to build:

.. code-block:: shell

    $ export USER=<your githost username>
    $ export PASS=<your githost password>
    $ export KEY=<your githost token>
    $ export EVE_URL=<url of the instance of Eve>

    $ build

The helper will ouptut the URL to the new build in Eve.

Force stage helper
------------------

We can extend the previous script to pass extra parameters to the build. One
usage is for example to force the stage to run in the build, rather than
using the default stage induced from the branch name. Create the following
script ``build_stage`` for example:

.. code-block:: shell

    #!/bin/bash
    set -u

    STAGE=$1
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    PAYLOAD="{\"branch\":\"$BRANCH\",\"force_stage\":\"$STAGE\"}"

    reply=$(eve_api_client --username "${USER}" \
                           --password "${PASS}" \
                           --consumer-key "${KEY}" \
                           --base-url "${EVE_URL}" \
                           --httpmethod post \
                           --payload "${PAYLOAD}" \
                           /forceschedulers/force)

    # reply format is json:
    # {"id": 999, "jsonrpc": "2.0", "result": [345, {"2": 345}]}
    BUILDREQUEST=$(echo "${reply}" | jq -r '.result[0]')

    echo "${EVE_URL}/#/buildrequests/${BUILDREQUEST}?redirect_to_build=true"

Call this script from the repository and branch you would like to build, and
specify as an argument the stage to build:

.. code-block:: shell

    $ export USER=<your githost username>
    $ export PASS=<your githost password>
    $ export KEY=<your githost token>
    $ export EVE_URL=<url of the instance of Eve>

    $ build_stage mystage

Query the latest results
------------------------

The previous examples were targetting the /forceschedulers API endpoint to
start builds remotely. We can also query Buildbot's database to extract
useful intelligence on the recent builds. The script ``get_results`` will
print to the console the results of the builds:

.. code-block:: shell

    #!/bin/bash
    set -u

    reply=$(eve_api_client --username "${USER}" \
                           --password "${PASS}" \
                           --consumer-key "${KEY}" \
                           --base-url "${EVE_URL}" \
                           /builds)

    echo "${reply}" | jq -r '.builds[] | "\(.buildid): \(.state_string)"'

Call this script to check recent build results:

.. code-block:: shell

    $ export USER=<your githost username>
    $ export PASS=<your githost password>
    $ export KEY=<your githost token>
    $ export EVE_URL=<url of the instance of Eve>

    $ get_results | tail -n 5
    103: failed triggered cluster_1_9_6
    104: build successful
    105: failed 'helm install ...' (failure)
    106: failed triggered pre-merge
    107: build successful
