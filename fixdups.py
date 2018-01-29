import os, re, fnmatch, glob
picBaseDir = "\\Users\\Marty\\Pictures"

n = 0

def scandir(path):
    global n
    #print("Scanning "+path)
    printScanning = True
    dname = os.path.basename(path).split()[0]
    if not (dname == "D14S" or dname == "D14Z" or dname == "D16S" or dname == "D17B" or dname == "D17G" or dname == "DOC"):
        list = os.listdir(path)
        #num = 1
        for item in list:
            itempath = os.path.join(path, item)
            if os.path.isdir(itempath):
                scandir(itempath)
            else:
                name, ext = os.path.splitext(item)
                ext = ext.lower()
                match = re.match(r"(D[0-9A-Z]+-[0-9]+-.*)(-[0-9]{1,2})$", name)
                if match:
                    if printScanning:
                        print("Scanning "+path)
                        printScanning = False
                    os.chdir(path)
                    newname = match.groups()[0] + ext
                    os.rename(item, newname)
                    print("renaming {} to {}".format(item, newname))
                    #num += 1
                    n += 1

scandir(picBaseDir)

print("did {} items".format(n))
