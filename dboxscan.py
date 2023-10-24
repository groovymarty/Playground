import os, sys, re, fnmatch, shutil, time

mkdirs = 0
numcopied = 0
numfilerem = 0
numdirrem = 0
addcmds = []
delcmds = []
newer = []
newer_life = []
totsize = 0
sizelimit = 1000000000
sizelimited = False
dirs_scanned = {}

doAdds = True
doDels = True

myBaseDir = "D:\\DboxScan"
wastebase = os.path.join(myBaseDir, "Deleted-Files")
logPath = os.path.join(myBaseDir, "dboxscan.log")

log = open(logPath, mode="a", encoding="utf-8")
pendlog = ""

def logit(str):
    global pendlog
    if pendlog != "":
        tmp = pendlog
        pendlog = ""
        logit(tmp)
    print(str)
    print(str, file=log)

logit("----------------------------------------------")
logit("DboxScan on " + time.strftime("%c"))

def makedir(targpath):
    global mkdirs
    logit("Creating directory "+os.path.basename(targpath))
    #addcmds.append('mkdir -p "'+targpath+'"')
    os.makedirs(targpath)
    mkdirs += 1
    
def copyfile(srcpath, targpath, why):
    global numcopied
    logit("Copying "+os.path.basename(srcpath)+" ("+why+")")
    if doAdds:
        shutil.copyfile(srcpath, targpath)
        shutil.copystat(srcpath, targpath)
    else:
        addcmds.append('cp -p "'+srcpath+'" "'+targpath+'"')
    numcopied += 1

def targisnewer(srcpath, targpath):
    if os.path.join([Documents, Life]) in srcpath:
        logit("Duplicating "+os.path.basename(srcpath)+" because target file is newer")
        base, ext = os.path.splitext(srcpath)
        srcpath = base + "-dropbox" + ext
        shutil.copyfile(targpath, srcpath)
        shutil.copystat(targpath, srcpath)
        newer_life.append(srcpath)
    else:
        logit("Skipping "+os.path.basename(srcpath)+" because target file is newer")
        newer.append('cp -p "' + srcpath + '" "' + targpath + '"')
        #newer.append(targpath)
        #shutil.copystat(srcpath, targpath)

# usually we skip files and dirs only on the source side (local disk, not dropbox)
# this way they'll be cleaned up (not skipped) if they show up on dropbox
def skipdir(folder, dname, isSrc=True):
    if "iTunes" in folder:
        if dname == "Podcasts" or dname == "Album Artwork":
            return isSrc
    if folder.endswith("SlideShows"):
        return isSrc
    if folder.endswith("Documents"):
        # not sure we need this...
        if dname == "My Music" or dname == "My Pictures" or dname == "My Videos":
            return isSrc
    if dname == ".git" or dname == "__pycache__" or dname == "node_modules" or dname == "cache" or dname == "_hq":
        return isSrc
    return False

def skipfile(folder, fname, isSrc=True):
    if fname == "desktop.ini" or fname == "Thumbs.db":
        return isSrc
    if "SlideShows" in folder:
        ext = os.path.splitext(fname)[1]
        if ext == ".pxc" or ext == ".mov" or ext == ".avi" or ext == ".iso" or ext.startswith(".b"):
            return isSrc
    if folder.endswith("Pictures"):
        if fname.endswith(".php"):
            return True #always skip .php file (never delete them)
    return False

def movetowaste(targpath):
    (targdir, targname) = os.path.split(targpath)
    if re.match(r"[A-Za-z]:", targdir):
        targdir = targdir[2:]
    while targdir.startswith(os.sep):
        targdir = targdir[1:]
    wastepath = os.path.join(wastebase, targdir)
    if not os.path.exists(wastepath):
        os.makedirs(wastepath)
    uniqname = targname
    while os.path.exists(os.path.join(wastepath, uniqname)):
        match = re.match(r"(.*)__(\d+)$", uniqname)
        if match:
            n = int(match.group(2)) + 1
            uniqname = match.group(1)+("__%03d" % n)
        else:
            uniqname = uniqname+"__001"
    shutil.move(targpath, os.path.join(wastepath, uniqname))

def extrafile(targpath):
    global numfilerem
    logit("Extra file "+targpath)
    if doDels:
        movetowaste(targpath)
    else:
        delcmds.append('rm "'+targpath+'"')
    numfilerem += 1

def extradir(targpath):
    global numdirrem
    logit("Extra directory "+targpath+'"')
    if doDels:
        movetowaste(targpath)
    else:
        delcmds.append('rm -rf "'+targpath+'"')
    numdirrem += 1

def scandir(srcdir, targdir, exclude=[]):
    global totsize, sizelimited, pendlog
    dirs_scanned[targdir] = True
    scanning = "Scanning "+srcdir
    print(scanning)
    logged = False
    if not os.path.exists(targdir):
        makedir(targdir)
    srclist = os.listdir(srcdir)
    for item in srclist:
        if totsize > sizelimit:
            sizelimited = True
            break
        srcpath = os.path.join(srcdir, item)
        targpath = os.path.join(targdir, item)
        if os.path.isdir(srcpath):
            #print(srcpath+" is dir")
            if item in exclude or skipdir(srcdir, item) or targpath in dirs_scanned:
                continue
            if not os.path.exists(targpath):
                makedir(targpath)
            scandir(srcpath, targpath)
        else:
            #print(srcpath+" is file")
            if skipfile(srcdir, item):
                continue
            if not logged:
                pendlog = scanning
            if not os.path.exists(targpath):
                copyfile(srcpath, targpath, "new file")
                totsize += int(os.path.getsize(srcpath))
            else:
                srctime = int(os.path.getmtime(srcpath))
                srcsize = int(os.path.getsize(srcpath))
                targtime = os.path.getmtime(targpath)
                targsize = os.path.getsize(targpath)
                # one-second fuzz for time comparison
                if srctime > (targtime + 1.0):
                    copyfile(srcpath, targpath, "time dif")
                    totsize += srcsize
                elif srctime < (targtime - 1.0):
                    targisnewer(srcpath, targpath)
                elif srcsize != targsize:
                    copyfile(srcpath, targpath, "size dif")
                    totsize += srcsize
            if pendlog == "":
                logged = True
            else:
                pendlog = ""
    for item in os.listdir(targdir):
        if not item in srclist:
            targpath = os.path.join(targdir, item)
            if os.path.isdir(targpath):
                if not skipdir(targdir, item):
                    extradir(targpath)
            else:
                if not skipfile(targdir, item):
                    extrafile(targpath)

def finish():
    if sizelimited:
        print("That's enough for now!")
    print()
    logit("{} directories made".format(mkdirs))
    logit("{} files copied".format(numcopied))
    logit("{} bytes copied".format(totsize))
    logit("{} files removed".format(numfilerem))
    logit("{} directories removed".format(numdirrem))
    logit("{} newer files skipped (see newer.sh)".format(len(newer)))
    for path in newer_life:
        logit("*** Dropbox file is newer, please check: {}".format(path))
            
    with open(os.path.join(myBaseDir, "addcmds.sh"), mode="w", encoding="utf-8") as f:
        for command in addcmds:
            print(command, file=f)
            
    with open(os.path.join(myBaseDir, "delcmds.sh"), mode="w", encoding="utf-8") as f:
        for command in delcmds:
            print(command, file=f)
            
    with open(os.path.join(myBaseDir, "newer.sh"), mode="w", encoding="utf-8") as f:
        for fname in newer:
            print(fname, file=f)

    log.close()
    print()
    input("I am finished.  You may close this window.")

