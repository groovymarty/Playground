# shoebox.nailcache

import os
from shoebox.nails import Nails, read_nails
from tkit import environ

cache = {}
cacheCount = 0
touchCount = 0

def get_nails(folderPath, sz, env=None):
    global cacheCount, touchCount
    folderPath = os.path.abspath(folderPath)
    if sz not in cache:
        cache[sz] = {}
    if folderPath in cache[sz]:
        nails = cache[sz][folderPath]
    else:
        nails = Nails(read_nails(folderPath, sz))
        cache[sz][folderPath] = nails
        cacheCount += 1
        environ.log_info(env, "Added '{}' sz={:d} to nail cache, n={}".format(folderPath, sz, cacheCount))

    # touch for LRU algorithm
    nails.touch(touchCount)
    touchCount += 1
    return nails

# clear nails from cache, all sizes
def clear_nails(folderPath, env=None):
    global cacheCount
    folderPath = os.path.abspath(folderPath)
    for sz in cache:
        if folderPath in cache[sz]:
            del cache[sz][folderPath]
            cacheCount -= 1
            environ.log_info(env, "Removed '{}' sz={:d} from nail cache, n={}".format(folderPath, sz, cacheCount))

looseCache = {}
looseCount = 0

def add_loose_file(path, sz, img):
    global looseCount
    path = os.path.abspath(path)
    if sz not in looseCache:
        looseCache[sz] = {}
    looseCache[sz][path] = img
    looseCount += 1

def get_loose_file(path, sz):
    path = os.path.abspath(path)
    if sz in looseCache and path in looseCache[sz]:
        return looseCache[sz][path]
    else:
        return None

def change_loose_file(oldPath, newPath):
    oldPath = os.path.abspath(oldPath)
    newPath = os.path.abspath(newPath)
    for sz in looseCache:
        if oldPath in looseCache[sz]:
            looseCache[sz][newPath] = looseCache[sz][oldPath]
            del looseCache[sz][newPath]

# clear loose file from cache
def clear_loose_file(path, sz):
    path = os.path.abspath(path)
    global looseCount
    if sz in looseCache:
        if path in looseCache[sz]:
            del looseCache[sz][path]
            looseCount -= 1

# add thumbnails to loose file cache, all sizes
def explode_nails(folderPath):
    folderPath = os.path.abspath(folderPath)
    for sz in cache:
        if folderPath in cache[sz]:
            nails = cache[sz][folderPath]
            for name, data in nails.get_all():
                add_loose_file(os.path.join(folderPath, name), sz, data)
