# shoebox.metacache

import os
from shoebox.metadict import MetaDict
from shoebox import pic
from tkit import environ

cache = {}
cacheCount = 0
touchCount = 0

def get_meta_dict(folderPath, env=None, okToCreate=True):
    global cacheCount, touchCount
    folderPath = os.path.abspath(folderPath)
    if folderPath in cache:
        metaDict = cache[folderPath]
    else:
        try:
            metaDict = MetaDict(folderPath, env, okToCreate)
        except FileNotFoundError:
            # only happens if okToCreate is false
            return None
        cache[folderPath] = metaDict
        cacheCount += 1
        environ.log_info(env, "Added '{}' to meta cache, n={}".format(folderPath, cacheCount))

    # touch for LRU algorithm
    metaDict.touch(touchCount)
    touchCount += 1
    return metaDict

def clear_meta_dict(folderPath, env=None):
    """clear meta dictionary from cache"""
    global cacheCount
    folderPath = os.path.abspath(folderPath)
    if folderPath in cache:
        del cache[folderPath]
        cacheCount -= 1
        environ.log_info(env, "Removed '{}' from meta cache, n={}".format(folderPath, cacheCount))

def write_all_changes(env=None):
    """write all changed dictionaries"""
    for folderPath, metaDict in cache.items():
        metaDict.write(env)

looseCache = {}
looseCount = 0

def add_loose_meta(path, meta):
    global looseCount
    path = os.path.abspath(path)
    if path not in looseCache:
        looseCount += 1
    looseCache[path] = meta

def get_loose_meta(path, remove=False):
    global looseCount
    path = os.path.abspath(path)
    if path in looseCache:
        meta = looseCache[path]
        if remove:
            del looseCache[path]
            looseCount -= 1
        return meta
    else:
        return None

def change_loose_meta(oldPath, newPath):
    global looseCount
    oldPath = os.path.abspath(oldPath)
    newPath = os.path.abspath(newPath)
    if oldPath in looseCache:
        if newPath in looseCache:
            looseCount -= 1
        looseCache[newPath] = looseCache[oldPath]
        del looseCache[oldPath]

def clear_loose_meta(path):
    """clear loose meta from cache"""
    global looseCount
    path = os.path.abspath(path)
    if path in looseCache:
        del looseCache[path]
        looseCount -= 1

def remove_meta_to_loose_cache(path, env=None):
    """find metadata for specified file, remove from its dictionary and add to loose cache"""
    dirname, name = os.path.split(path)
    parts = pic.parse_file(name, env)
    if parts:
        metaDict = get_meta_dict(dirname, env, okToCreate=False)
        if metaDict:
            metaDict.remove_meta(parts.id, path)
