Builds, stages & workers
========================

In buildbot, a build is a list of steps executed sequentially on a given worker.
Each build can trigger multiple other builds (which allow to run tasks
concurently).
A pipeline ends up looking like a tree of nested builds.

In eve some builds have special meaning, so a special vocabulary is used to
refer to them.

The first build (started either by a webhook or a force form) is called
`Bootstrap`, it runs a number of eve internal steps automatically (settings some
environment, parsing the yaml file...) and then decide to trigger a build
according to the instruction written in eve/main.yml.

Any builds below the bootstrap is called a "stage" in eve.
The first stage called by bootstrap according to the branch mapping in
eve/main.yml is the one the reporter will send build status update for.

Then this main stage can trigger any number of other stages (which in turn can
do just that do) with the special `TriggerStage` step.

When clicking on a status badge on github/bitbucket, you are directly redirected
to the top-level stage so you won't see the bootstrap (and probably will never
have to worry about it).

In eve UI, the stages are folded by default. You can fold/unfold them to see the
details of their steps execution by clicking the '>' arrows.
