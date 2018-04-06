import re


def convert_to_bytes(size):
    try:
        return int(size)
    except ValueError:
        pass

    size = size.upper()
    m = re.search(r'^([0-9]+)([BKMG])[BI]?$', size)
    if not m:
        raise ValueError('size could not be parsed')

    size_digits = m.group(1)
    size_unit = m.group(2)

    size_bytes = int(size_digits)
    for unit in ['B', 'K', 'M', 'G']:
        if size_unit == unit:
            break
        size_bytes = 1024 * size_bytes

    return size_bytes


def convert_to_cpus(cpu):
    m = re.search(r'^([0-9]+(?:\.[0-9]+)?)(m?)$', cpu)
    if not m:
        raise ValueError('cpu amount could not be parsed')

    res = float(m.group(1))
    if m.group(2):
        res /= 1000
    return res
