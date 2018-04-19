Frequently asked questions
==========================

How do I force a build on a branch?
-----------------------------------

``builds`` -> ``builders`` -> ``bootstrap`` -> ``force`` -> enter your branch's name



How do I force a build on a commit?
-----------------------------------

Currently, eve refuses to build a commit that is not a tip of a branch. You need
to create a user/* branch pointing on it and push it. The results will be
accessible from the bitbucket interface: https://bitbucket.org/scality/<your
repo>/branches/


How do I relaunch only tests and not builds on a given build/sha1 ?
-------------------------------------------------------------------

A branch has been created especially for this case: user/qa/post-merge

You have to provide two parameters :

   * ``force_artifacts_name``: e.g. bitbucket:scality:ring:promoted-7.1.0_rc3

   * ``force_test_branch``: usually development/something

See screenshot below :

.. TODO add screenshot and update this part


Can I have parameterized builds?
--------------------------------

Not yet. Buildbot allows it but we need to add a layer in eve to expose buildbot's capabilities.

.. TODO yes we can now


Can I have access to the workers?
---------------------------------

Yes and no. There is no easy way to do it today with eve. We need to give root
access to the platform. It is a bit dangerous so we avoid doing it for everybody
in the company but will definitely do on demand.


How can I get help?
-------------------

The HipChat ``Community support (RELENG projects)`` room is the place to go. The
Release Engineering team dedicates one person every day (The Night's Watch lord
Commander) to answer questions in this room.
