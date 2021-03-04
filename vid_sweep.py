# vid_sweep

# Scan folders for video files and check for various things

from os.path import dirname
import sys, os, shutil, subprocess
from shoebox import pic

picturesDir="D:\\Users\\msaus\\Pictures"
fourMb = 4096 * 1024

dirMap = {}
vidMap = {}
hqVidMap = {}

def checkEmptyHqFolder(id):
    i = id.find("-")
    if i > 0:
        folderId = id[0:i]
        dir = dirMap[folderId]
        if dir:
            hqDir = os.path.join(dir, "_hq")
            if os.path.exists(hqDir) and len(os.listdir(hqDir)) == 0:
                print("deleting empty folder:", hqDir)
                os.rmdir(hqDir)

def scandir(path, isHq=False):
    global n
    print("Scanning "+path)
    list = os.listdir(path)
    for item in list:
        itempath = os.path.join(path, item)
        if os.path.isfile(itempath):
            parts = pic.parse_file(item)
            if parts and parts.id and parts.ext.lower() in pic.videoExts:
                sz = os.path.getsize(itempath)
                if isHq:
                    hqVidMap[parts.id] = {"name": item, "path": itempath, "size": sz}
                else:
                    vidMap[parts.id] = {"name": item, "path": itempath, "size": sz}
        elif os.path.isdir(itempath) and not item.startswith("_"):
            parts = pic.parse_folder(item)
            if parts and parts.id:
                dirMap[parts.id] = itempath
                scandir(itempath)
        elif os.path.isdir(itempath) and item.startswith("_hq"):
            scandir(itempath, True)

scandir(picturesDir)
print("found videos: {0} std, {1} hq".format(len(vidMap), len(hqVidMap)))
print("hq videos without std:")
n = 0
for id, hqVid in hqVidMap.items():
    if not id in vidMap:
        print("{0}".format(hqVid["name"]))
        n += 1
print("found", n)
print("hq videos not significantly bigger than std:")
n = 0
nfix = 0
for id, hqVid in hqVidMap.items():
    if id in vidMap:
        vid = vidMap[id]
        dif = hqVid["size"] - vid["size"]
        if hqVid["size"] < fourMb or (dif < fourMb and dif / vid["size"] < 0.5 and vid["size"] < fourMb*2):
            print("{0}: {1}k, std {2}k".format(hqVid["name"], hqVid["size"]//1024, vid["size"]//1024))
            n += 1
            if id.startswith("D19"):
                print("removing", vid["path"])
                os.remove(vid["path"])
                print("moving", hqVid["path"], "to", vid["path"])
                os.rename(hqVid["path"], vid["path"])
                checkEmptyHqFolder(id)
                nfix += 1
print("found", n, "fixed", nfix)
