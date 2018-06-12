Overview
========

Eve is a continuous integration tool that can run arbitrary pipelines on commits
of a Git repository. It is constructed as a software layer above Buildbot. It
enriches Buildbot’s feature set, notably by using code in the built repository
itself to define the pipeline.

This lets developpers update their CI pipeline without needing the independently
of the platform operator.

Currently, eve is able to spawn openstack workers, docker workers and kubernetes
workers.

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
