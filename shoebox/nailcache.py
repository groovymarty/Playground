# shoebox.nailcache

from shoebox.nails import Nails, read_nails

cache = {}
touchCount = 0

def get_nails(folderPath, sz):
    global touchCount
    key = (folderPath, sz)
    if key in cache:
        nails = cache[key]
    else:
        print("adding {} {:d} to cache".format(folderPath, sz))
        nails = Nails(read_nails(folderPath, sz))
        cache[key] = nails

    # touch for LRU algorithm
    nails.touch(touchCount)
    touchCount += 1
    return nails
