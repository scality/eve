First steps with Eve
====================

Install Eve for your repository
-------------------------------

.. TODO

Bootstrap the build definition file
-----------------------------------

.. TODO

Run the first manual build
--------------------------

Make sure that the eve user has access to your repo as well as its git modules.

.. TODO

Store build artifacts securely
------------------------------

.. TODO

Automate builds
---------------

.. TODO rewrite section

Add a webhook to your github/bitbucket.
.. TODO add exact url syntax and describe how to do it using bitbucket’s
.. interface (go to settings -> webhooks -> etc.)).

Using GitHub’s interface:

    * Go to ``https://github.com/<owner>/<repo>/settings/hooks``

    * Click the ``Add webhook button``

    * Payload URL: ``https://eve.devsca.com/github/<owner>/<repo>/change_hook/github``

    * Content type : ``application/json``

    * Click the green ``Add webhook`` button to validate




