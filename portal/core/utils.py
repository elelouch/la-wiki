from itertools import chain

@staticmethod
def flatten_perms(perms_qs):
    bidimensional_perms = [gp.permissions.all() for gp in perms_qs]
    return list(chain.from_iterable(bidimensional_perms))

