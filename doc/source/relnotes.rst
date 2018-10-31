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

Eve 1.3.47 (2018-10-31)
=======================

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
