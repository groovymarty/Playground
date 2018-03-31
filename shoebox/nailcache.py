# shoebox.nailcache

from shoebox.nails import Nails, read_nails
from tkit import environ

cache = {}
cacheCount = 0
touchCount = 0

def get_nails(folderPath, sz, env=None):
    global cacheCount, touchCount
    if sz not in cache:
        cache[sz] = {}
    if folderPath in cache[sz]:
        nails = cache[sz][folderPath]
    else:
        nails = Nails(read_nails(folderPath, sz))
        environ.log_info(env, "Adding '{}' sz={:d} to nail cache, n={}".format(folderPath, sz, cacheCount))
        cache[sz][folderPath] = nails
        cacheCount += 1

    # touch for LRU algorithm
    nails.touch(touchCount)
    touchCount += 1
    return nails

def invalidate_nails(folderPath, env=None):
    for sz in cache:
        if folderPath in cache[sz]:
            del cache[sz][folderPath]

looseCache = {}
looseCount = 0

def add_loose_file(path, sz, img):
    global looseCount
    if sz not in looseCache:
        looseCache[sz] = {}
    looseCache[sz][path] = img
    looseCount += 1

def get_loose_file(path, sz):
    if sz in looseCache and path in looseCache[sz]:
        return looseCache[sz][path]
    else:
        return None

def change_loose_file(oldPath, newPath):
    for sz in looseCache:
        if oldPath in looseCache[sz]:
            looseCache[sz][newPath] = looseCache[sz][oldPath]
            del looseCache[sz][oldPath]
