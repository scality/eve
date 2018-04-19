How does eve work?
==================

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

1. build number.

2. relaunch builds. Note that only “bootstrap” (or “root”) builds can be rebuilt
   (buildbot notion of build is slightly different than a pipeline run; the
   pipeline will contain one bootstrap build and several sub-builds, in buildbot
   terminology). Build failures can be categorized as “normal” (the pipeline
   caught an error in the code of the commit), environmental issues (frequent
   when the pipeline relies on external sources), or test flakiness (tests that
   fail, but not always, and the failure may not be related to the changes in
   the commit). For the later two, it is good practice to take a look at the
   logs and try to fix the flakiness or, at least file a bug. Flakiness is
   a very annoying technical debt and we need to keep it at its minimum.

3. the duration field shows you the build duration when the build is running and
   then shows you the build's age.

4. Build page tabs

   * Build steps shows you the shape of your pipeline as designed in
     eve/main.yml file. We will go through its details later.

   * Build properties shows you a dictionary of keys/values of variables that
     can be used by your pipeline. Properties are similar to environment
     variables but are `more powerful`_. You can add/update your own properties
     but there are some provided to you by eve/buildbot from scratch:

     - branch name

     - git sha1

     - ...
   * Worker tab: gives you some information on the worker that executed the
     stage. In this example, it is a docker container.

   * Responsible users: Who did the git push?

   * Changes: Which git changes triggered the build?

   * Debug: Some extra-debug information (buildbot version, buildbot master
     name, ...)

.. _more powerful: http://docs.buildbot.net/latest/manual/cfg-properties.html

5. The build block:

   In buildbot, a build is a list of steps executed sequentially on a given
   worker. The most common steps allow to run a shell command. It is not
   possible to parallelize steps within the same build.

   What you can do, however, is to add a 'Trigger' step to launch one or more
   sub-builds on other workers, and in parallel. The parent build can wait for
   the results of its sub builds, check their results and decide to
   continue/halt. Child builds can also have children and the final shape of
   your pipeline looks like a directory tree.

   eve uses this system to build a pipeline from the yaml file. Every webhook
   triggers a build named 'bootstrap'. 'bootstrap' loads the yaml file and
   triggers your pipeline's top-level build and this top-level build may, in
   turn trigger other child builds::

       1 bootstrap build -> 1 top-level build -> 0..n child builds

   As you can see, for buildbot all the builds and their children are called
   builds.

   At RelEng, we've found out that this is confusing, especially for end users.
   The wording 'build' refers to different things depending on the context. We
   prefer calling the top-level block the top-level stage and all of its
   children "stages". For instance, in the eve/main.yaml file, we only refer to
   stages. In eve's language, the line above becomes::

       1 bootstrap -> 1 top-level stage -> 0..n stages

   When you click on a status badge on github/bitbucket, you are directly
   redirected to the top-level stage (and not the bootstrap). The bootstrap
   contains internal steps barely useful for developers.

   The top-level's stage description here is 'pre-merge'. Please use this
   description in your eve/main.yaml files. This is part of a bigger plan to
   have pre-merge and post-merge pipelines (quick/slow tests).

   On the right side, we can access the corresponding bootstrap if you are
   curious or if you want to rebuild it.

6. The stages:

   The stages are folded by default. You can unfold them to see the details of
   their steps.
