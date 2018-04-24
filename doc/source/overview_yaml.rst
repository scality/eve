Build definition file
=====================

An eve/main.yml file may look like this:

.. code-block:: yaml
   :caption: eve/main.yml
   :linenos:

   version: 0.2
   branches:
    user/*, feature/*, improvement/*, bugfix/*, w/*, q/*:
      stage: pre-merge
    development/*:
      stage: post-merge

   stages:
     pre-merge:
      worker:
        type: docker
        path: eve/workers/trusty
        volumes:
          - '/home/eve/workspace'
      steps:
        - TriggerStages:
            name: static checks and test stages simultaneously
            stage_names:
              - static checks
              - system tests
     static checks:
      worker:
        type: docker
        path: eve/workers/trusty
        volumes:
          - '/home/eve/workspace'
      steps:
        - Git:
            name: fetch source
            repourl: "%(prop:git_reference)s"
            shallow: True
            retryFetch: True
        - ShellCommand:
            name: run static analysis tools
            command: tox --sitepackages -e flake8,prospector,pylint
     system tests:
      worker:
        type: openstack
        image: Ubuntu 16.04 LTS (Xenial Xerus) (PVHVM)
        flavor: general1-4
        path: eve/workers/system_tests
      steps:
        - Git:
            name: fetch source
            repourl: "%(prop:git_reference)s"
            shallow: True
            retryFetch: True
        - ShellCommand:
            name: upgrade pip
            command: sudo -H pip install --upgrade pip
            haltOnFailure: True
        - ShellCommand:
            name: install mysql client
            command: sudo apt-get install -qy libmysqlclient-dev
            haltOnFailure: True
        - ShellCommand:
            name: install tox
            command: sudo -H pip install tox==2.3.2
            haltOnFailure: True
        - ShellCommand:
            name: run tests
            command: HOME=/home/eve tox -e systemtests
            logfiles:
              master0.twistd.log: /home/eve/.eve_test_data/master0/twistd.log
              master1.twistd.log: /home/eve/.eve_test_data/master1/twistd.log
              master2.twistd.log: /home/eve/.eve_test_data/master2/twistd.log
            lazylogfiles: True
            haltOnFailure: True
     post-merge:
      worker:
        type: docker
        path: eve/workers/trusty
        volumes:
          - '/home/eve/workspace'
      steps:
        '......' # removed some redundant content
        - ShellCommand:
            name: run tests
            command: HOME=/home/eve tox -e slowtests
            logfiles:
              master0.twistd.log: /home/eve/.eve_test_data/master0/twistd.log
              master1.twistd.log: /home/eve/.eve_test_data/master1/twistd.log
              master2.twistd.log: /home/eve/.eve_test_data/master2/twistd.log
            lazylogfiles: True
            haltOnFailure: True

Pretty intuitive, isn't it?

line 1
    The eve's yaml version. Eve is young and is evolving fast. Adding a version
    number allows us to change the design and make non-retrocompatible changes
    while avoiding to break the branches that contain old yaml files.
    Currently, 0.2 is the latest and greatest version.

lines 2-6
    The branch wildcard based stage selector. If your current branch matches one
    of the wildcards, than, the bootstrap will trigger the corresponding
    top-level stage. We strongly recommend using the branch selectors and the
    stage names that are given in the example above. This will help the
    integration of Bert-E.

lines 8-85
    Stages definition. Here you will find all the stage definitions that need to
    be started by eve.

line 9, 21, 36 and 69
    The `pre-merge`, `static checks` and `post-merge` stages use a docker
    worker. The Dockerfile is under eve/workers/trusty.

    The `system tests` stage uses an openstack worker. The image name and the
    flavor (machine specs) are available on `rackspace's website`_.
    Please choose the smallest machine that suit your needs. Machines are
    expensive.
    An openstack machine takes about 5 minutes to start and is automatically
    killed after +/- 3 hours if your build is stuck.

    The steps definition is magic. The list of yaml steps is automagically
    converted to buildbot steps. For a detailed documentation on the available
    steps and their respective parameters, you can refer to `Buildbot's
    documentation on build steps`_.

.. _Buildbot's documentation on build steps:
    http://docs.buildbot.net/latest/manual/cfg-buildsteps.html
.. _rackspace's website: https://www.rackspace.com/openstack/public/pricing


Examples of yaml files
----------------------

.. TODO display files

RING: https://bitbucket.org/scality/ring/src/addd7f8f0a4c698dcf3f0deb9abfb3ef149d1845/eve/main.yml

EVE: https://bitbucket.org/scality/eve/src/9d0a7425ecec2be751bc65367dd6522f808f8fd5/eve/main.yml?at=development%2F1.0&fileviewer=file-view-default

BERT-E: https://bitbucket.org/scality/eve/src/9d0a7425ecec2be751bc65367dd6522f808f8fd5/eve/main.yml?at=development%2F1.0&fileviewer=file-view-default
