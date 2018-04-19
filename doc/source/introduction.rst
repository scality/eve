What is eve?
============

.. TODO add image

eve is a builder that can run arbitrary pipelines on commits of a Git
repository. It is constructed as a software layer above Buildbot.It enriches
Buildbot’s feature set to fit Scality's needs. Currently, eve is able to spawn
openstack workers and docker workers. AWS support is also planned.

Today, eve is managing an infrastructure with peaks reaching 700 CPUs used
simultaneously (1500 docker containers and 80 VMs).

Eve is now open source and its code is available on bitbucket_.

The deployment code is written in ansible and salt. It is available in the
repository pipeline-deploy_.

.. _bitbucket: https://bitbucket.org/scality/eve
.. _pipeline-deploy: https://bitbucket.org/scality/pipeline-deploy/src


Why Buildbot?
=============

Many CI tools are structured as ready-to-use applications. Users fill in
specific details, such as version control information and build process, but the
fundamental design is fixed and options are limited to those envisioned by the
authors. This arrangement suits the common cases quite well: there are
cookie-cutter tools to automatically build and test Java applications, Ruby
gems, and so on. Such tools embody assumptions about the structure of the
project and its processes. They are not well-suited to more complex cases, such
as mixed-language applications or complex release tasks, where those assumptions
are violated.

Buildbot must be seen more as a library than a ready-to-use tool. It offers you
a maximum of flexibility to build your pipeline. Basically, if you need to add
a feature, you need to create a Python class that inherits from one of
buildbot's core classes and change their behavior. Extremely powerful!

Another great feature in buildbot is that it uses a database to store all of its
data. The database's model is available and allows us to get stats, to monitor
and to troubleshoot issues.
