Troubleshooting guide
=====================

When I access the build's page, it is blank.
--------------------------------------------

You'll need to authenticate (top-left corner). Buildbot does not display an
error when you are not authenticated. It just gives access to nothing.


I could not authenticate. eve keeps sending me back to the blank page.
----------------------------------------------------------------------

This is a known issue when we upgrade buildbot's version. Browser cookies from
version ``n`` are not compatible with ``n+1``. You'll need to delete some
cookies and retry.


My build did not start. What should I do?
-----------------------------------------

1. You need to check if the webhook is installed on your git repo.

2. You need to check that the webhooks were sent by bitbucket/github and
   received a 20X response (200 OK or 202 Added). If you see HTTP errors (40X
   responses) there, please contact RelEng as these are indicative of
   a deployment issue.

3. You need to check that eve is responding
   ``https://eve.devsca.com/<github/bitbucket>/scality/<repo-name>``

4. Sometimes the build request is received by eve but takes some time to send
   the ``IN PROGRESS`` status build to bitbucket/github. Waiting a little bit.

   This happens in a couple of cases:

   * Eve's capacity is exceeded and your build is waiting in eve's queue. You
     easily check that by clicking ``builder`` -> ``bootstrap``. If you see the
     'build requests' (gray dots) section, that means that eve is in queueing
     mode. You can even find your build request.

   * Eve's docker cache has been deleted and it is rebuilding a new one. Eve has
     started the bootstrap job but did not reach the first stage yet.
     Notifications are sent at the beginning of the first stage. You easily
     check that by clicking ``builder`` -> ``bootstrap``. Go through the yellow
     dots to see if you build is among them.

Other possibilities are:

    * buildbot has lost its TCP connection to crossbar.io (a service allowing to
      sync multiple buildbot masters). When this happens, buildbot needs to be
      restarted (`contact RelEng`_).

    * A network failure caused the loss of the github/bitbucket webhook. Retry
      or force the build.

    * Your commit is not a tip of a branch anymore. Another commit has been
      pushed on top of it.

    * A bug in eve/buildbot (`contact RelEng`_).

.. _contact RelEng: mailto:releng@scality.com
