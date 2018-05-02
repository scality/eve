Overview
========

Eve is a builder that can run arbitrary pipelines on commits of a Git
repository. It is constructed as a software layer above Buildbot. It enriches
Buildbot’s feature set to fit Scality's needs. Currently, Eve is able to spawn
openstack workers, docker workers and kubernetes workers.

Today, Eve is managing an infrastructure build around Kubernetes with peaks
reaching around 130 nodes.

Eve is open source and its code is available on bitbucket_.

.. _bitbucket: https://bitbucket.org/scality/eve

.. toctree::
   :caption: Contents:
   :name: overview_toc
   :maxdepth:   1

   overview/eve
   overview/build
   overview/yaml
   overview/ui
   overview/artifacts
   overview/secrets
   overview/stats
