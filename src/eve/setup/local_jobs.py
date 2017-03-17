from ..utils.local_jobs import get_local_jobs


def setup_local_jobs(local_workers, master_name):
    return get_local_jobs(
        local_workers,
        suffix="-{0}".format(master_name)
    )
