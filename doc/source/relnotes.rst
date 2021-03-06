Release Notes
~~~~~~~~~~~~~

..
    Don't write directly to this file!
    Eve use towncrier to manage its release notes.
    You should instead add a file in eve/newsfragment directory named following
    this pattern: <JIRA-TICKET>-whatever-you-want.<type>
    The available types are:
      * feature
      * bugfix
      * doc
      * removal
      * misc
    At release time, the release notes are then generated using:
    tox -e relnotes <eve-version>

.. towncrier release notes start

Eve 1.7.8 (2021-04-15)
======================

Bugfixes
--------

- Fix doc image generation. (EVE-1154)


Eve 1.7.7 (2021-04-14)
======================

Features
--------

- Fix buildbot-worker install for Centos8 OpenStack worker. (EVE-1149)


Eve 1.7.6 (2020-12-17)
======================

Features
--------

- Add support for default value in prop in "doStepIf". (EVE-1141)


Eve 1.7.5 (2020-06-11)
======================

Features
--------

- Accept '-' character in promotion tag. (RELENG-3822)
- Promotion doc updated to include artifacts v3 procedure. (EVE-1130)


Eve 1.7.4 (2020-04-08)
======================

Features
--------

- Adding new properties ``builderid`` and ``buildurl`` which can be useful to find the build url. (EVE-1126)


Eve 1.7.3 (2020-04-03)
======================

Features
--------

- Added explanation for 404 returned by last_success. (RELENG-3665)


Eve 1.7.2 (2020-03-25)
======================

Features
--------

- Allow to promote a promoted build. (EVE-1124)
- Allow to define region based image mapping. Useful for scality.cloud (RELENG-2975)


Bugfixes
--------

- Repair artifacts upload retry. (PIPDEP-866)


Eve 1.7.1 (2020-02-21)
======================

Bugfixes
--------

- Rework ``GetArtifactsFromStage`` regex to support artifacts V3 response. (EVE-1120)


Eve 1.7.0 (2020-02-19)
======================

Features
--------

- ``Upload`` step is now using artifacts version >= 3 only. (EVE-1114)
- Use "artifacts" service for promote and prolong operations. (RELENG-3593)


Eve 1.6.3 (2020-02-05)
======================

Features
--------

- Use "artifacts-v3" service for promote and prolong operations. (EVE-1115)


Eve 1.6.2 (2020-02-03)
======================

Features
--------

- Created a new step ``SetWorkerDistro`` which is now implicitly called on each stage instantiation to identify the worker linux distribution and set new properties. (EVE-1112)


Bugfixes
--------

- Fixed the space encoding in artifacts uploading. (EVE-1110)
- Modifying xargs opts on ``UploadV3`` step depending on linux OS distribution. (EVE-1112)


Eve 1.6.1 (2020-01-21)
======================

Features
--------

- Prefix UploadV3 step name with ``V3``. (EVE-1113)


Bugfixes
--------

- Fixed nginx behaviour refusing an uri with two spaces. (EVE-1110)
- Made find command compatible with busybox. (EVE-1111)
- Modify xargs opts on Artifacts Upload Version 3 so that it is compatible with Alpine. (EVE-1112)


Eve 1.6.0 (2020-01-20)
======================

Features
--------

- Adding the ability to simultaneously upload artifacts into version 2 and 3 at the same time. (EVE-1109)
- Adding new step ``Uploadv3`` to handle artifacts version >= 3 upload. (EVE-1109)
- Added temporary promotion button. (PIPDEP-827)
- Added promotion button. (PIPDEP-829)


Eve 1.5.15 (2019-12-11)
=======================

Bugfixes
--------

- Setting up a proper name on every docker container created so that we don't have to handle regex matching to figure it out. (EVE-1023)


Eve 1.5.14 (2019-12-06)
=======================

Bugfixes
--------

- To ease up investigation on docker failures we are adding a new log to the worker. (EVE-1023)


Eve 1.5.13 (2019-12-04)
=======================

Features
--------

- Add support for setting ``doStepIf`` and ``hideStepIf`` with build properties. (EVE-1104)


Eve 1.5.12 (2019-12-04)
=======================

Bugfixes
--------

- We're poping all eve configuration from the environment to avoid them to be displayed in the UI. (EVE-1097)
- Fixed Ubuntu bionic image spawn. (EVE-1103)


Eve 1.5.11 (2019-10-08)
=======================

Bugfixes
--------

- Now when a Dockerfile is outside a Docker build context it is computed as well in the fingerprint. (EVE-1098)


Eve 1.5.10 (2019-09-24)
=======================

Features
--------

- Add a new type of menu item ('static') to dump the contents of a local file.
  (RELENG-2975)


Eve 1.5.9 (2019-09-05)
======================

Bugfixes
--------

- Reverting new ``requirements.sh`` install and putting it back on the cloud init side. (EVE-1080)


Eve 1.5.8 (2019-08-28)
======================

Bugfixes
--------

- Upgrading twisted to ``19.7.0`` to fix writeSequence errors. (EVE-1083)


Eve 1.4.11 (2019-09-20)
=======================

Features
--------

- Add a new type of menu item ('static') to dump the contents of a local file.
  (RELENG-2975)


Eve 1.4.10 (2019-08-28)
=======================

Bugfixes
--------

- Add report_path option to Junitshellcommand. (EVE-1085)


Eve 1.5.7 (2019-08-20)
======================

Features
--------

- Bringing the ``simultaneous_builds`` parameter on a stage to let the user control the pipeline. (RELENG-2859)


Eve 1.5.6 (2019-08-02)
======================

Including changes from Eve 1.4.9

Eve 1.4.9 (2019-08-02)
======================

Features
--------

- Supporting file as payload on eve API client script. (EVE-1074)


Bugfixes
--------

- Add buildbot fix to send less SQL queries to the db server. (EVE-1082)


Eve 1.5.5 (2019-07-01)
======================

Including changes from Eve 1.4.8


Eve 1.4.8 (2019-07-01)
======================

Features
--------

- Remove janitor expensive and useless write operations. (RELENG-3038)


Bugfixes
--------

- Reverting bootstrap notifications. (EVE-1071)

Eve 1.5.4 (2019-06-21)
======================

Including changes from Eve 1.4.7

Eve 1.4.7 (2019-06-21)
======================

Features
--------

- Apply the new janitor that will be available in buildbot > 2.3.1.
  (RELENG-3038)
- Reporting bootstrap failures to githost
  (EVE-1071)


Bugfixes
--------

- Ensure that production_version and artifacts_name are correctly formatted.
  (EVE-1065)
- Build status should be skipped when a branch is not covered by the CI.
  (EVE-1076)

Eve 1.5.3 (2019-06-19)
======================

Features
--------

- Setup the requirements step on the Openstack worker as a ``ShellCommand``. (EVE-1056)


Eve 1.5.2 (2019-05-20)
======================

Bugfixes
--------

- Rework ``kube_pod`` worker naming due to conflicts when triggering
  multiple stage at the same time. (EVE-1064)


Eve 1.5.1 (2019-05-16)
======================

Including changes from Eve 1.4.6


Eve 1.4.6 (2019-04-24)
======================

Features
--------

- Adding the possibility to setup Buildbot's Janitor in order to clean up old
  logs. (EVE-1053)
- Allow compatibility with pip>=10 (EVE-970)


Bugfixes
--------

- Fix hard limit on ``main.yml`` config files. (EVE-1013)
- Fix a typo that broke the configuration for Cron Builders with Github.
  (EVE-1042)


Eve 1.5.0 (2019-03-27)
======================

Features
--------

- Implementing the buildbot concept of ``virtual_builder`` therefore improving the UI. (EVE-949)
- Allow compatibility with pip>=10 (EVE-970)
- Upgrading eve to Buildbot ``2.0.1`` and the base version of Python to ``3.6``. (EVE-970)


Eve 1.4.5 (2019-02-28)
======================

Features
--------

- Support redhat images with the Openstack worker. (RING-29139)


Bugfixes
--------

- Removing ``yum distro-sync`` commands on yum based images for the openstack
  worker. (EVE-1040)


Eve 1.4.4 (2019-02-22)
======================

Bugfixes
--------

- Now installing a missing dependency in the ``eve_api_client`` Docker image.
  (EVE-1038)


Eve 1.4.3 (2019-02-06)
======================

Features
--------

- Add a script that retrieves artifacts from a failed build (optionally with a
  step or stage name) and attaches them to the requested JIRA Issue. (EVE-1021)
- Remove hipchat reporter. (EVE-1028)
- Remove ultron reporter. (EVE-1029)


Bugfixes
--------

- Updating frozen dependencies to fix docker compose build step. (EVE-1030)


Eve 1.4.2 (2018-11-30)
======================

Features
--------

- Add env vars for docker-hook. (RELENG-2721)


Eve 1.3.48 (2018-11-23)
=======================

Bugfixes
--------

- Revert changes on api client (PIPDEP-595) due to broken compatibilites.
  (EVE-1017)


Eve 1.3.47 (2018-11-22)
=======================

Bugfixes
--------

- Fix unexpected data type error when using unicode string on kube_pod worker.
  (EVE-1016)


Eve 1.4.0 (2018-10-31)
======================

Features
--------

- Add Helm charts for Eve. (PIPDEP-595)
- Refactor and extend capabilities of Openstack init scripts. (PIPDEP-595)
- Update default value of FORCE_BUILD_PARAM_COUNT: 0 -> 2. (PIPDEP-595)
- Remove phony configuration variable NGROK. (PIPDEP-595)
- Deprecate conf setting CLOUD_INIT_SCRIPT (was unused since introduction of
  Heat). (PIPDEP-595)
- Deprecate MICROSERVICE* conf settings (replaced with better OpenStack and
  Kube interfaces). (PIPDEP-595)
- Add conf setting KUBE_POD_GITCONFIG_CM. (PIPDEP-595)


Eve 1.3.46 (2018-10-22)
=======================

Bugfixes
--------

- Ensure that kube pods worker are actually gone when deleting them from the
  cluster. (EVE-1008)


Eve 1.3.45 (2018-10-19)
=======================

Features
--------

- Setup the property ``worker_uuid`` on all worker types. (EVE-983)
- Add Helm charts for eve-cron-builder, a microservice based on eve-api-client.
  (PIPDEP-595)
- Add Helm charts for documentation. (PIPDEP-595)
- Import improvements on eve-api-client from Bert-E 3.2.0 (PIPDEP-595):
    - support for python 3
    - better authentication flow on Bitbucket
    - better autodetection of git host.


Bugfixes
--------

- Remove deprecated env variable CLOUDFILES_URL. (PIPDEP-595)


Eve 1.3.44 (2018-09-14)
=======================

Bugfixes
--------

- Show progress bar while uploading artifacts to prevent being killed for
  output timeout. (PIPDEP-590)


Eve 1.3.43 (2018-09-04)
=======================

Features
--------

- Support building images with dockerfiles path different from build context on
  ``kube_pod`` workers. (EVE-990)


Eve 1.3.42 (2018-08-09)
=======================

Bugfixes
--------

- Prevent docker and openstack worker auto-retry in case of known permanent
  failure. (EVE-964)
- Support Openstack keystoneauthv3 API authentication. (EVE-989)


Eve 1.3.41 (2018-08-06)
=======================

Features
--------

- Document mechanism to archive artifacts. (EVE-959)
- Deprecate ShellCommandWithSecrets. (EVE-966)
- Update troubleshooting in documentation regarding frozen steps. (EVE-984)


Bugfixes
--------

- When starting the bootstrap, check there is not index.lock left by a previous
  git command. (EVE-963)
- Fixing cloud init script to avoid race condition on ip routes. (PIPDEP-551)


Eve 1.3.40 (2018-07-03)
=======================

Features
--------

- Amend artifacts documentation (simplified example and un-branding). (EVE-354)
- Bootstrap some documentation for the new secret manager. (EVE-354)
- Document get_product_version script. (EVE-959)
- Update FAQ. (EVE-959)
- Interpolate secrets inside a ``kube_pod`` worker. (EVE-962)
- Added a dynamic mapping of image and flavor values for heat stack workers.
  (RELENG-2672)


Bugfixes
--------

- Fix github reporter sending build status for every stage. (EVE-957)
- Fail generation of release notes if version is not specified. (EVE-959)


Eve 1.3.39 (2018-06-15)
=======================

Bugfixes
--------

- Fix a bug crashing reporters when formatting the end status of a build.
  (PIPDEP-393)


Eve 1.3.38 (2018-06-13)
=======================

Features
--------

- Add possibility to restrain vault secrets to a namespace via secretsmount and
  VAULT_FILE. (EVE-354)


Bugfixes
--------

- Remove references to proprietary code or business specific concepts.
  (EVE-954)
- Moved additionnals non-core services to a new `Services` section. (EVE-954)
- Overhaul of the whole `first steps` and `Overview` sections. (EVE-954)
- Fix boot of Docker container in standalone mode. (PIPDEP-393)


Eve 1.3.37 (2018-06-06)
=======================

Bugfixes
--------

- Fix Wheezy VM worker support. (RELENG-2650)


Eve 1.3.36 (2018-06-04)
=======================

Features
--------

- Fix Centos6 VM spawn. (RELENG-2650)
- Support Scality Cloud. (RELENG-2650)


Bugfixes
--------

- Ensure docker images contain untouched code, so that git tags are rid of
  'dirty' mention. (EVE-953)
- Fix documentation container generation. (PIPDEP-492)


Eve 1.3.35 (2018-05-28)
=======================

Features
--------

- Verify generation of release notes in CI. (EVE-839)
- Simplify mechanism of reporters. (EVE-951)
- Prevent users from using a stage name `bootstrap` and pre-check validity of
  stages. (EVE-951)


Bugfixes
--------

- Fix bootstrap_reason property and update reason property. (EVE-948)
- Fix reporters in the case the master is a KubeLatentWorker or Local worker.
  (EVE-951)


Eve 1.3.34 (2018-05-15)
=======================

Bugfixes
--------

- Fix a regression that broke the rebuild form request. (EVE-950)


Eve 1.3.33 (2018-05-14)
=======================

Bugfixes
--------

- Revert EVE-948 due to regression on the UI. Now adding a new field
  ``bootstrap_reason`` to identify the build reason inside any stage. (EVE-948)


Eve 1.3.32 (2018-05-04)
=======================

Features
--------

- Show version in interface (About). (EVE-839)
- Add Kubernetes cluster service. It is now possible to request a service in
  the Pod workers. When requested, Eve will invoke the service setup
  micro-service (if configured), and configure the pod to access that external
  cluster. (EVE-887)


Bugfixes
--------

- Inherit the reason property from bootstrap. (EVE-948)


Eve 1.3.31 (2018-04-25)
=======================

Features
--------

- Add dry run mode on api client. (EVE-840)
- Add ``kube_pod`` as new worker type that can spawn a complex kubernetes pod
  from a given spec yaml file. (EVE-891)
- Add new steps SetBootstrapProperty and SetBootstrapPropertyFromCommand.
  (PIPDEP-436)


Bugfixes
--------

- No longer duplicate the docker steps launched before a TriggerStage.
  (EVE-891)


Improved Documentation
----------------------

- Bootstrap Eve's user doc. (EVE-839)


Eve 1.3.30 (2018-04-03)
=======================


Features
--------

- Add github support in eve-api-client. (EVE-882)
- Add reason "branch updated" to builds triggered by a webhook (new push).
  (EVE-875)


Eve 1.3.29 (2018-03-23)
=======================


Features
--------

- Drop sentry support. (EVE-840)

Bugfixes
--------

- Fix adapting Eve to kubernetes upgrade. (PIPDEP-431)

Eve 1.3.28 (2018-03-20)
=======================


Features
--------

- Add memory request option to docker worker in main.yml. (PIPDEP-364)


Bugfixes
--------

- Fix Ultron reporter sending 'failed' when the build was in progress.
  (RELENG-2469)
- Fix Ultron not sending the correct build url in statuses. (RELENG-2469)


Eve 1.3.27 (2018-02-26)
=======================


Features
--------

- Move docker-hook service to an external repository. (RELENG-2456)

Eve 1.3.26 (2018-02-22)
=======================


Features
--------

- Add a docker image for eve-api-client. (PIPDEP-360)
- Allow to use absolute path for source of `Upload` step. (EVE-833)
- The source of `Upload` step can now use interpolable property too. (EVE-832)


Bugfixes
--------

- Inherit properties' source as well as value in sub-stages. It also fix
  overrideable properties. (EVE-815)
- Fix high memory footprint of uploading context to docker-hook causing `docker
  build` commands to be killed. (PIPDEP-391)


Eve 1.3.25 (2018-02-09)
=======================


Features
--------

- All Eve defined properties can now be overriden by user when doing a force
  build (Added steps `EveProperty` and `EvePropertyFromCommand` to let the user
  define overrideable properties too). (EVE-815)


Eve 1.3.24 (2018-02-01)
=======================


Features
--------

- Retry when the docker hook is not ready. (EVE-819)


Eve 1.3.23 (2018-01-17)
=======================


Bugfixes
--------

- Fix docker-hook code that was removed during the review.

Eve 1.3.22 (2018-01-15)
=======================


Features
--------

- Allow to trigger any stage in forced build, ignoring the branch assigned
  stage. (EVE-815)
- Prettier force build form. (EVE-815)
- Automatic replacement of illegal character in label provided by skari.
  (EVE-811)


Bugfixes
--------

- `GetArtifactsFromStage` now properly fails when no artifacts can be found.
  (EVE-815)


Eve 1.3.21 (2018-01-11)
=======================


Features
--------

- Force builds are always executed. (EVE-815)


Eve 1.3.20 (2018-01-10)
=======================


Bugfixes
--------

- Fix docker separator. (EVE-811)


Eve 1.3.19 (2018-01-05)
=======================


Bugfixes
--------

- Fix retries crashing the backend on restart. (EVE-800)
- Don't overwrite gitconfig in docker worker. (PIPDEP-339)


Eve 1.3.18 (2017-12-13)
=======================


Features
--------

- Add Ultron reporter. (EVE-771)


Bugfixes
--------

- Fix infinite crash loop on failed docker build during worker substantiation. (EVE-708)


Eve 1.3.17 (2017-12-04)
=======================


Bugfixes
--------

- Fix an issue with unicode in step names.


Eve 1.3.16 (2017-11-29)
=======================


Features
--------

- Set locale in cloud init before running buildbot.


Eve 1.3.15 (2017-11-28)
=======================


Bugfixes
--------

- Fix a rare bug caused by Eve local git clone not being properly cleaned
  between two builds. (EVE-805)


Eve 1.3.14 (2017-11-24)
=======================


Features
--------

- Add last chance cleanup of leftover children containers when finishing
  a docker worker stage. (PIPDEP-307)


Bugfixes
--------

- Don't block docker hook waiting for irremediably lost workers. (EVE-801)


Eve 1.3.13 (2017-11-20)
=======================


Features
--------

- Add configuration option for stage to be watched by reporters. (EVE-762)


Eve 1.3.12 (2017-11-14)
=======================


Features
--------

- Using worker node pool on docker-hook. (PIPDEP-302)

Bugfixes
--------

- Lift limits to avoid crashes on docker-hook. (EVE-795)


Eve 1.3.11 (2017-11-10)
=======================


Features
--------

- Increase artifacts `Upload` default timeout from 15 minutes to 1 hour.
  (EVE-788)
- Allow main.yml to specify a `maxTime` timeout for `Upload` step. (EVE-788)
- Allow access to `max_step_timeout` throuhg a property. (EVE-786)


Bugfixes
--------

- Fix incorrect `SECRET_*` env var stripping. (EVE-791)


Eve 1.3.10 (2017-10-25)
=======================


Features
--------

- Add an option to customize docker worker's deadline. (EVE-752)


Bugfixes
--------

- Avoid clashing docker worker names. (EVE-752)


Eve 1.3.9 (2017-10-23)
======================


Features
--------

- Allow artifacts microservice to live on subpath. (PIPDEP-256)
- Tag docker worker with project name. (PIPDEP-264)
- Docker worker async delete. (PIPDEP-264)
- Hardcode ODR max workers. (PIPDEP-264)


Eve 1.3.8 (2017-10-17)
======================


Features
--------

- Upgrade to buildbot 0.9.12. (EVE-671)
- Add metabase dashboard in Eve's UI. (EVE-687)


Bugfixes
--------

- Fix possible crash during docker build step. (EVE-754)


Eve 1.3.7 (2017-10-06)
======================


Features
--------

- Make sure kubectl client and server match on docker-hook. (EVE-687)
- More robust docker kill on docker-hook. (EVE-687)


Eve 1.3.6 (2017-10-05)
======================


Features
--------

- Allow skipping branches or stages matching a regexp given during runtime.
  (EVE-687)


Bugfixes
--------

- Fix docker hook unicode handling. (EVE-746)
- Fix docker build retry when triggering a stage. (EVE-751)
- Fix docker hook command return code. (EVE-750)


Eve 1.3.5 (2017-09-26)
======================


Features
--------

- Add more volumes types support to docker hook. (EVE-687)
- Add stop/kill capabilities to docker hook. (EVE-687)


Bugfixes
--------

- Fix Github reporter. (EVE-743)


Eve 1.3.4 (2017-09-20)
======================


Features
--------

- Add artifacts and gitcache microservices for VM. (EVE-715)
- Handle all docker commands via docker hook. (EVE-414)
- Openstack heat worker path is now optional. (EVE-738)
- Add buildnumber to worker name and labels. (EVE-687)
- Hide registry related steps in UI. (EVE-687)
- Replace `HOSTALIASES` with dynamic `artifacts_private_url` property. (EVE-715)


Bugfixes
--------

- Improve long step names cut to take interpolates into account. (EVE-698)
- Hide env vars in bootstrap steps. (EVE-649)
- Properly mark `GetArtifactsFromStage` step as failed when the curl request
  failed. (EVE-715)


Eve 1.3.3 (2017-08-25)
======================


Features
--------

- Add bitbucket OAuth-based Eve api client. (EVE-709)


Bugfixes
--------

- Trim long step names to avoid DB insertion errors. (EVE-698)
- Relay docker hook exceptions to Eve. (EVE-687)


Eve 1.3.2 (2017-08-08)
======================


Features
--------

- Add garbage collection to gitcache service. (EVE-699)
- Allow `image` in docker steps to contain interpolable property. (EVE-703)


Bugfixes
--------

- Avoid forking in gitcache services to be able to capture commands' output.
  (EVE-660)
- Fix retry logic and increase initial quarantine timeout on Eve latent workers.
  (EVE-680)
- Fix heat worker insubstantiation error reporting. (EVE-702)
- Fix git LFS authentication issues. (EVE-678)


Eve 1.3.1 (2017-07-27)
======================


Features
--------

- Modify docker hook to run as a sidecar container. (EVE-687)


Eve 1.3.0 (2017-07-21)
======================


Features
--------

- New Eve infrastructure based on Kubernetes.
