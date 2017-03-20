from buildbot.plugins import util


def setup_local_jobs(local_workers, master_name):
    return util.get_local_jobs(
        local_workers,
        suffix="-{0}".format(master_name)
    )
