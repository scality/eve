Overview
========

Eve is a builder that can run arbitrary pipelines on commits of a Git
repository. It is constructed as a software layer above Buildbot.It enriches
Buildbot’s feature set to fit Scality's needs. Currently, eve is able to spawn
openstack workers and docker workers. AWS support is also planned.

Today, eve is managing an infrastructure with peaks reaching 700 CPUs used
simultaneously (1500 docker containers and 80 VMs).

Eve is open source and its code is available on bitbucket_.

.. _bitbucket: https://bitbucket.org/scality/eve

.. toctree::
   :caption: Contents:
   :name: overview_toc
   :maxdepth:   1

   overview_eve
   overview_build
   overview_yaml
   overview_ui
   overview_artifacts
   overview_secrets
   overview_stats
