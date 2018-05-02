Builds, stages & workers
========================

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

First, you need to configure your github/bitbucket repository to send webhooks
to eve (See "How to register a new git repository ?" section below). eve listens
to github/bitbucket webhooks triggered by "git push" events.

