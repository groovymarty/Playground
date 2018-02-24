# shoebox.nailcache

from shoebox.nails import Nails, read_nails
from tkit import environ

cache = {}
cacheCount = 0
touchCount = 0

def get_nails(folderPath, sz, env=None):
    global cacheCount, touchCount
    key = (folderPath, sz)
    if key in cache:
        nails = cache[key]
    else:
        cacheCount += 1
        environ.log_info(env, "Adding '{}' sz={:d} to nail cache, n={}".format(folderPath, sz, cacheCount))
        nails = Nails(read_nails(folderPath, sz))
        cache[key] = nails

    # touch for LRU algorithm
    nails.touch(touchCount)
    touchCount += 1
    return nails
