import os, re, fnmatch, glob
picBaseDir = "\\Users\\Marty\\Pictures"

fbat = open("\\Scratch\\undo_fixdups2.bat", "w")

def scandir(path):
    #print("Scanning "+path)
    ids = dict()
    list = os.listdir(path)
    for item in list:
        itempath = os.path.join(path, item)
        if os.path.isdir(itempath):
            scandir(itempath)
        else:
            match = re.match(r"^([A-Z]+[0-9]*[A-Z]*)(_?[0-9]*)-([A-Z]*)(0*)([1-9][0-9]*)([A-Z]*)([- ]*)([^.]*)(.*)", item)
            if match:
                (parent, child, type, zeros, num, ver, sep, comment, ext) = match.groups()
                id = parent + child + "-" + type + num + ver
                #print(id)
                if id in ids:
                    #print("found duplicate "+id)
                    ids[id].append(item)
                else:
                    ids[id] = [item];
    n = 0
    for id in ids:
        if len(ids[id]) > 1:
            items = ids[id]
            #print("duplicates:")
            items.sort(key=len)
            items.pop(0)
            i = ord('A')
            for item in items:
                #print(chr(i)+": "+item)
                match = re.match(r"^([A-Z]+[0-9]*[A-Z]*)(_?[0-9]*)-([A-Z]*)(0*)([1-9][0-9]*)([A-Z]*)([- ]*)([^.]*)(.*)",
                                 item)
                if match:
                    (parent, child, type, zeros, num, ver, sep, comment, ext) = match.groups()
                    if ver:
                        print("# ALREADY HAS VERSION: "+item)
                    newitem = parent + child + "-" + type + zeros + num + ver + chr(i) + sep + comment + ext
                    #print(newitem)
                    if n == 0:
                        print("cd "+path, file=fbat)
                    print("ren \""+newitem+"\" \""+item+"\"", file=fbat)
                    os.rename(os.path.join(path, item), os.path.join(path, newitem))
                    n += 1
                    i += 1


scandir(picBaseDir)
fbat.close()
