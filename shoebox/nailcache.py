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

def clear_nails(folderPath, env=None):
    """clear nails from cache, all sizes"""
    global cacheCount
    folderPath = os.path.abspath(folderPath)
    for sz in cache:
        if folderPath in cache[sz]:
            del cache[sz][folderPath]
            cacheCount -= 1
            environ.log_info(env, "Removed '{}' sz={:d} from nail cache, n={}".format(folderPath, sz, cacheCount))

looseCache = {}
looseCount = 0

def add_loose_file(path, sz, imgOrData):
    """loose file cache can take PIL image or PNG data bytes"""
    global looseCount
    path = os.path.abspath(path)
    if sz not in looseCache:
        looseCache[sz] = {}
    if path not in looseCache[sz]:
        looseCount += 1
    looseCache[sz][path] = imgOrData

def get_loose_file(path, sz):
    path = os.path.abspath(path)
    if sz in looseCache and path in looseCache[sz]:
        return looseCache[sz][path]
    else:
        return None

def change_loose_file(oldPath, newPath):
    global looseCount
    oldPath = os.path.abspath(oldPath)
    newPath = os.path.abspath(newPath)
    for sz in looseCache:
        if oldPath in looseCache[sz]:
            if newPath in looseCache[sz]:
                looseCount -= 1
            looseCache[sz][newPath] = looseCache[sz][oldPath]
            del looseCache[sz][oldPath]

def clear_loose_file(path, sz=None):
    """clear loose file from cache"""
    if sz is None:
        for sz in looseCache:
            clear_loose_file(path, sz)
    else:
        path = os.path.abspath(path)
        global looseCount
        if sz in looseCache:
            if path in looseCache[sz]:
                del looseCache[sz][path]
                looseCount -= 1

def explode_nails(folderPath):
    """add thumbnails to loose file cache, all sizes"""
    folderPath = os.path.abspath(folderPath)
    for sz in cache:
        if folderPath in cache[sz]:
            nails = cache[sz][folderPath]
            for name, data in nails.get_all():
                # note here we are storing PNG data bytes in loose file cache
                add_loose_file(os.path.join(folderPath, name), sz, data)
