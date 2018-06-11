First steps with Eve
====================

Install Eve for your repository
-------------------------------

Eve needs some additional microservice to work properly. So the easiest way to
deploy it is to use the salt scripts in pipeline-deploy_ repository.

It can setup properly a complete eve service and all required cronjob and
microservices required in a kubernetes cluster.

Please refer to its README for more information on how to use the salt scripts.

.. _pipeline-deploy: https://bitbucket.org/scality/pipeline-deploy

Bootstrap the build definition file
-----------------------------------

At the root of your repository, create the following tree of files:

::

    eve
    ├── main.yml
    └── workers
        └── master
            └── Dockerfile

The Dockerfile must define a container that start a buildbot-worker (see
`Buildbot's Worker Setup`_), has git installed (to pull the repository) and
curl available (to upload the artifacts).

.. _Buildbot's Worker Setup: http://docs.buildbot.net/latest/manual/installation/worker.html

Then start writing your pipeline in `eve/main.yml`.
A minimal pipeline would looks like this:

.. code-block:: yaml
   :caption: eve/main.yml

   version: 0.2
   branches:
    default:
      stage: pre-merge

   stages:
     pre-merge:
      worker:
        type: docker
        path: eve/workers/master
        volumes:
          - '/home/eve/workspace'
      steps:
        - Git:
            name: fetch source
            repourl: "%(prop:git_reference)s"
            shallow: True
            retryFetch: True
        - ShellCommand:
            name: run some tests
            command: <here-your-test-suite-command>

For more informations on the yaml file structure, refer to the YAML overview and
the Build steps reference guide of this documentation.

Run the first manual build
--------------------------

Make sure that the eve user has access to your repo as well as its git modules.

Then either push some code to the repository or force a manual build.

Automate builds
---------------

At some point you'll probaply want Eve to automatically start building commit
when new code is pushed to the repository.
To achieve that, you need to configure your github/bitbucket repository to send
webhooks to eve.

On GitHub:

    * Go to ``https://github.com/<owner>/<repo>/settings/hooks``

    * Click the ``Add webhook button``

    * Payload URL: ``https://<eve_base_url>/github/<owner>/<repo>/change_hook/github``

    * Content type : ``application/json``

    * Click the green ``Add webhook`` button to validate

On Bitbucket:

    * Go to ``https://bitbucket.com/<owner>/<repo>/admin/addon/admin/bitbucket-webhooks/bb-webhooks-repo-admin``

    * Click the ``Add webhook button``

    * URL: ``https://<eve_base_url>/bitbucket/<owner>/<repo>/change_hook/bitbucket``

    * Triggers: ``Repository push``

    * Click the ``Save`` button to validate
