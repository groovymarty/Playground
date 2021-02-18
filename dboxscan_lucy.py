import dboxscan, os

basedir = os.path.join("D:\\Users","jills")
dboxdir = os.path.join(basedir,"DropBox")

def scanone(srctail, targtail, exclude=[]):
    dboxscan.scandir(os.path.join(basedir, srctail), os.path.join(dboxdir, targtail), exclude)

scanone("Documents", os.path.join("Jill", "Documents"), ["Archives", "GitHub", "Life", "Teaching"])
basedir = os.path.join(basedir, "Documents")
scanone("Archives", "Archives")
scanone("Life", "Life")
scanone("Teaching", "Teaching")
basedir = os.path.join("C:\\Users","jills")
scanone("Desktop", os.path.join("Jill", "Desktop_lucy"))

dboxscan.finish()
