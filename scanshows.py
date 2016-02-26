import os, fnmatch

def scandir(srcdir):
    print("Scanning "+srcdir)
    srclist = os.listdir(srcdir)
    for item in srclist:
        if fnmatch.fnmatch(item, "*.psh"):
            srcpath = os.path.join(srcdir, item)
            filebase = os.path.splitext(item)[0]
            vidpath = os.path.join(srcdir, filebase+".mp4")
            status = ""
            if os.path.exists(vidpath):
                srctime = os.path.getmtime(srcpath)
                vidtime = os.path.getmtime(vidpath)
                if srctime > (vidtime + 1.0):
                    status = "Out of date"
            else:
                status = "No video"
            if status:
                print("** "+filebase+" ("+status+")")
            else:
                print("   "+filebase)
                                        
scandir("c:\\Users\\Marty\\Documents\\Slide Shows")
