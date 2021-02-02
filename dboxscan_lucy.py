import dboxscan, os

basedir = os.path.join("D:\\Users","jills")
dboxdir = os.path.join(basedir,"DropBox")

def scanone(srctail, targtail, exclude=[]):
    dboxscan.scandir(os.path.join(basedir, srctail), os.path.join(dboxdir, targtail), exclude)

scanone("Documents", os.path.join("Jill", "Documents"), ["GitHub", "Life", "Teaching"])
scanone("Desktop", os.path.join("Jill", "Desktop_lucy"))
basedir = os.path.join(basedir, "Documents")
scanone("Life", "Life")
scanone("Teaching", "Teaching")

dboxscan.finish()
