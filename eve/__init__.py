from pkg_resources import DistributionNotFound, get_distribution

__all__ = ['__version__']


def get_version():
    try:
        return get_distribution('eve').version
    except DistributionNotFound:
        return 'dev'


__version__ = get_version()
