Handling secrets
================

Dealing with secrets in a CI is hard! Almost all the CI tools that we have used
store them in environment variables and try to obfuscate them from the logs. We
think that we can come up with something better.

So there is a *"What we want to do"* and a *"What we can do right now"*.


What we want to do
------------------

Every time an access to an external service is required, we develop a new step
that allows the developers to access the service without providing credentials.
Credentials are managed internally by eve.

This is already the case for the 'Git' clone step. No keys needed in the yaml
file. Everything is managed under the hood.

We also want to use Hashicorp's vault to store secrets. The PR has just been
`merged in buildbot`_. :)

.. _merged in buildbot: https://github.com/buildbot/buildbot/pull/2835


What we have now
----------------

For now, it is a bit more rustic. We define environment variables in the
`deployment script`_.

.. _deployment script: https://bitbucket.org/scality/pipeline-deploy/src/80f524135946a3b189f31959639699196ab8c3e0/salt/states/eve-master/init.sls?at=development%2F1.0&fileviewer=file-view-default

The env variables starting with ``SECRET_`` will be automatically obfuscated in
eve's log and UI. Secrets are stored in the deployment repository in
a PGP-protected file.

To add a secret, we need to add it to the deployment repo and the redeploy the
eve's masters. This stops the running jobs so we avoid doing it when there are
a lot of people using the platform.
