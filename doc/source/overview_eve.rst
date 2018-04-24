Yet another CI engine?
======================

Buildbot as the build engine
----------------------------

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

What is Eve?
------------
First, you need to configure your github/bitbucket repository to send webhooks
to eve (See "How to register a new git repository ?" section below). eve listens
to github/bitbucket webhooks triggered by "git push" events.

For every received webhook, eve checks out the relative git branch and looks in
the target repository for a yaml file, under ``eve/main.yaml``. This file will
dictate the behavior of the pipeline for that specific commit.

Depending on the presence/absence of ``eve/main.yaml`` and on its contents, eve
will eventually decide to start a build.

Once the build finished, eve will report its outcome to github/bitbucket using
their respective APIs, by setting a status on the commit that has entered the
pipeline. The build status is displayed on their web ui (see screenshots below).

.. TODO add images

Clicking on the status badges will take you to eve's interface (See screenshot
below). Note that, currently, eve can only be accessed from Scality's offices or
through the VPN. Some security holes discovered on buildbot are preventing us
from removing this constraint. However, this may change in the (not so far)
future.

.. TODO add screenshot

The screenshot above shows how a successful build looks like in the standard
buildbot interface

.. TODO bullet points

For every received webhook, eve checks out the relative git branch and looks in
the target repository for a yaml file, under ``eve/main.yaml``. This file will
dictate the behavior of the pipeline for that specific commit.

Depending on the presence/absence of ``eve/main.yaml`` and on its contents, eve
will eventually decide to start a build.

Once the build finished, eve will report its outcome to github/bitbucket using
their respective APIs, by setting a status on the commit that has entered the
pipeline. The build status is displayed on their web ui (see screenshots below).

.. TODO add images

Clicking on the status badges will take you to eve's interface (See screenshot
below). Note that, currently, eve can only be accessed from Scality's offices or
through the VPN. Some security holes discovered on buildbot are preventing us
from removing this constraint. However, this may change in the (not so far)
future.

.. TODO add screenshot

The screenshot above shows how a successful build looks like in the standard
buildbot interface
