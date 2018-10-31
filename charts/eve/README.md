# Eve

[Eve](https://bitbucket.org/scality/eve/) is a continuous integration framework
built above Buildbot. Declare your pipeline as data in the target repository
and let Eve build all your commits. Eve provides a unique support for highly
scalable builds running in a mix of containers, virtual machines and other
resources.


# Chart Developer notes

## How to add a new configuration value:

If a new configuration setting (NEW_CONF) is added to Eve master.cfg, add it
to the deployment as well, by creating a new entry in values.yaml:

    eve.masterConf.newConf

The camelCase `newConf` will be added to the environment of each master as the
UPPER_SNAKE_CASE `NEW_CONF` automatically (see printConf in `_helpers.tpl` to
understand how).

The configuration value will be stored in a config map.


## How to add a new _secret_ configuration value:

Building on top of the previous section, if newConf is a secret (and must
therefore be stored in a Secret file rather than a Config map), additionally
declare the new conf key in file `_secrets.txt`.

See printSecret in `_helpers.tps` for more details.


## How to add a new _file_ configuration value:

Lastly, if newConf contains a file to deploy rather than a conf setting or
secret, you can still declare the new value in the relevant section of
`values.yaml`. Additionally, you need to:

- declare the new key in file `_files.txt`,
- add the relevant code to deploy the file where appropriate in templates.
