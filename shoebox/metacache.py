# shoebox.metacache

import os
from shoebox.metadict import MetaDict
from tkit import environ

cache = {}
cacheCount = 0
touchCount = 0

def get_meta_dict(folderPath, env=None):
    global cacheCount, touchCount
    folderPath = os.path.abspath(folderPath)
    if folderPath in cache:
        metaDict = cache[folderPath]
    else:
        metaDict = MetaDict(folderPath, env)
        cache[folderPath] = metaDict
        cacheCount += 1
        environ.log_info(env, "Added '{}' to meta cache, n={}".format(folderPath, cacheCount))

    # touch for LRU algorithm
    metaDict.touch(touchCount)
    touchCount += 1
    return metaDict

# clear meta dictionary from cache
def clear_meta_dict(folderPath, env=None):
    global cacheCount
    folderPath = os.path.abspath(folderPath)
    if folderPath in cache:
        del cache[folderPath]
        cacheCount -= 1
        environ.log_info(env, "Removed '{}' from meta cache, n={}".format(folderPath, cacheCount))
