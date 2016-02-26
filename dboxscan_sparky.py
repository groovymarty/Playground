import dboxscan, os

basedir = os.path.join("\\Users","Marty")
dboxdir = os.path.join(basedir,"DropBox")

def scanone(srctail, targtail):
    dboxscan.scandir(os.path.join(basedir, srctail), os.path.join(dboxdir, targtail))

scanone("Documents\\Business", "Marty\\Business")
scanone("Documents\\Family Archives", "Family Archives")
scanone("Documents\\Grace", "Grace")
scanone("Documents\\Heidi", "Heidi")
scanone("Documents\\Jeff", "Jeff")
scanone("Documents\\Kermit", "Kermit")
scanone("Documents\\Lawsuit", "Lawsuit")
scanone("Documents\\Letters", "Marty\\Letters")
scanone("Documents\\Martin", "Martin")
scanone("Documents\\Organ", "Organ")
scanone("Documents\\Past Projects", "Marty\\Past Projects")
scanone("Documents\\Python", "Marty\\Python")
scanone("Documents\\Python Backup", "Marty\\Python Backup")
scanone("Documents\\PycharmProjects", "Marty\\PycharmProjects")
scanone("Documents\\Python Stable", "Python")
scanone("Documents\\SlideShows", "SlideShows")
scanone("Documents\\Various", "Marty\\Various")
scanone("Pictures", "Pictures")
scanone("Documents\\St Lukes Archives", "St Lukes Archives")
scanone("Music\\iTunes", "iTunes")

dboxscan.finish()
