import string
from random import choice


def password_generator(size=18, chars=string.ascii_uppercase + string.digits):
    return ''.join(choice(chars) for _ in range(size))
