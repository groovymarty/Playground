import dboxscan, os

basedir = os.path.join("\\Users","Jill")
dboxdir = os.path.join(basedir,"DropBox")

def scanone(srctail, targtail):
    dboxscan.scandir(os.path.join(basedir, srctail), os.path.join(dboxdir, targtail))

scanone("Documents\\Everybody", "Everybody")
scanone("Documents", os.path.join("Jill", "Documents"))
scanone("Desktop", os.path.join("Jill", "Desktop"))
basedir = "\\Jill"
scanone("Life", "Life")
scanone("Scatacook Shores HOA", "Scatacook Shores HOA")
scanone("Teaching", "Teaching")

dboxscan.finish()
