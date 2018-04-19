How to use eve with my git repository?
======================================

Create a pull request to add a section to `pipeline-deploy's pillar`_

.. _pipeline-deploy's pillar: https://bitbucket.org/scality/pipeline-deploy/src/80f524135946a3b189f31959639699196ab8c3e0/salt/pillars/repositories.sls?at=development%2F1.0&fileviewer=file-view-default

Make sure that the eve user has access to your repo as well as its git modules.

Add a webhook to your github/bitbucket.
.. TODO add exact url syntax and describe how to do it using bitbucket’s
.. interface (go to settings -> webhooks -> etc.)).

Using GitHub’s interface:

    * Go to ``https://github.com/<owner>/<repo>/settings/hooks``

    * Click the ``Add webhook button``

    * Payload URL: ``https://eve.devsca.com/github/<owner>/<repo>/change_hook/github``

    * Content type : ``application/json``

    * Click the green ``Add webhook`` button to validate

Sync with RelEng and wait for the next eve deployment (once every few days). If
you are in a hurry, we can speed-up things.

*Note:*
    *We're working on a continuous deployment method for eve. Changes will be
    applied on the run.*
