# vid_roundup

# This is a one-time use program which I wrote to help me deal with a folder
# of original video files.  My practice for a long time was to run video files
# through Handbrake to make them smaller and always mp4, then copy to their
# place in the Pictures folder structure.  This also resulted in their
# being saved to Dropbox.

# I saved the original video files in a folder called Originals, but
# they were never backed up or put anywhere.  Then I added support for
# "high quality" videos to the gvypics system.  The videos in the regular
# folders are "standard quality" (compressed for web).  An optional _hq
# folder can contain a "high quality" alternative file for each video.
# The hq videos are not saved in Dropbox, but they are copied to the
# Digital Ocean space (as are the regular video files).

# Now I can do something with those original video files.
# This program lists all the files in the Originals folder and gives options
# for processing each one:

# Move - Most of the original files are "straight from the camera" videos,
# much larger than the compressed files.  These are moved to the _hq folder.

# Delete - Some of the original files are very small videos saved from
# a text message.  These are deleted.

# Replace - In some cases the original videos were reasonably sized
# mp4 files.  I should not have run these through Handbrake, so the
# Replace button puts the original file in the picture folder.  There
# is no hq file in this case.

from os.path import dirname
import sys, os, shutil, subprocess
from shoebox import pic
from tkit import scrollableframe
from tkinter import *
from tkinter import ttk, filedialog, messagebox

picturesDir="D:\\Users\\msaus\\Pictures"
originalsDir="D:\\Users\\msaus\\Documents\\Video Projects\\Original"
deletedDir="D:\\Users\\msaus\\Documents\\Video Projects\\Deleted"
vlcPath="C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"
root = Tk()

dirMap = {}

def scandir(path):
    global n
    print("Scanning "+path)
    list = os.listdir(path)
    for item in list:
        itempath = os.path.join(path, item)
        if os.path.isdir(itempath) and not item.startswith("_"):
            parts = pic.parse_folder(item)
            if parts and parts.id:
                dirMap[parts.id] = itempath
                scandir(itempath)

scandir(picturesDir)

root = Tk()
frame = scrollableframe.ScrollableFrame(root)
sframe = frame.scrollable_frame

#frame.grid_columnconfigure(0, weight=1)
#frame.grid_rowconfigure(0, weight=1)
#delBtn = Button(root, text="Delete Found", command=do_delete)
#delBtn.grid(row=0, column=0, sticky=(N,W))
#text = Text(root)
#text.grid(row=1, column=0, sticky=(N,S,W,E))
#sb = Scrollbar(root, orient=VERTICAL, command=root.yview)
#sb.grid(row=0, column=1, sticky=(N,S))
#root['yscrollcommand'] = sb.set

list = os.listdir(originalsDir)

labels = []
entries = []
viewBtns = []
updateBtns = []
statuses = []
moveBtns = []
deleteBtns = []
replaceBtns = []

def doView(i):
    item = list[i]
    itempath = os.path.join(originalsDir, item)
    subprocess.run([vlcPath, itempath])

def getDirPath(i):
    str = entries[i].get()
    parts = parts = pic.parse_file(str)
    if not parts or not parts.id:
        statuses[i].config(text="parse failed")
        return None
    else:
        dir = parts.parent + parts.child
        dirPath = dirMap[dir]
        if not dirPath:
            statuses[i].config(text="{} not found".format(dir))
            return None
        else:
            path = os.path.join(dirPath, str)
            if not os.path.exists(path):
                statuses[i].config(text="{} not found".format(path))
                return None
            else:
                return dirPath

def doUpdate(i):
    dirPath = getDirPath(i)
    if dirPath:
        str = entries[i].get()
        path = os.path.join(dirPath, str)
        sz = round(os.path.getsize(path)/1024)
        statuses[i].config(text="{}K".format(sz))

def clearRow(i, what):
    labels[i].config(text="** "+what+" **")

# move video to _hq folder
def doMove(i):
    item = list[i]
    if item and not item.startswith("*"):
        itempath = os.path.join(originalsDir, item)
        dirPath = getDirPath(i)
        if dirPath:
            hqPath = os.path.join(dirPath, "_hq")
            if not os.path.exists(hqPath):
                os.mkdir(hqPath)
            str = entries[i].get()
            # use name from std video file with -hq inserted
            name, ext = os.path.splitext(str)
            # keep extension from hq video file
            dummy, itemext = os.path.splitext(item)
            newname = name + "-hq" + itemext
            destpath = os.path.join(hqPath, newname)
            print("moving {0} to {1}".format(itempath, destpath))
            os.rename(itempath, destpath)
            clearRow(i, "moved")

# move video to Deleted folder
def doDelete(i):
    item = list[i]
    if item and not item.startswith("*"):
        itempath = os.path.join(originalsDir, item)
        destpath = os.path.join(deletedDir, item)
        print("moving {0} to {1}".format(itempath, destpath))
        os.rename(itempath, destpath)
        clearRow(i, "deleted")

# replace existing std video file
def doReplace(i):
    item = list[i]
    if item and not item.startswith("*"):
        itempath = os.path.join(originalsDir, item)
        dirPath = getDirPath(i)
        if dirPath:
            str = entries[i].get()
            destpath = os.path.join(dirPath, str)
            print("removing {0}".format(destpath))
            os.remove(destpath)
            print("moving {0} to {1}".format(itempath, destpath))
            os.rename(itempath, destpath)
            clearRow(i, "replaced")

for i, item in enumerate(list):
    label = ttk.Label(sframe, text=item)
    label.grid(row=i, column=0)
    labels.append(label)
    itempath = os.path.join(originalsDir, item)
    sz = round(os.path.getsize(itempath)/1024)
    origSz = ttk.Label(sframe, text="{}K".format(sz))
    origSz.grid(row=i, column=1)
    viewBtn = ttk.Button(sframe, text="View", command=lambda i=i: doView(i))
    viewBtn.grid(row=i, column=2)
    viewBtns.append(viewBtn)
    entry = ttk.Entry(sframe)
    entry.grid(row=i, column=3)
    entries.append(entry)
    updateBtn = ttk.Button(sframe, text="Update", command=lambda i=i: doUpdate(i))
    updateBtn.grid(row=i, column=4)
    updateBtns.append(updateBtn)
    status = ttk.Label(sframe)
    status.grid(row=i, column=5)
    statuses.append(status)
    moveBtn = ttk.Button(sframe, text="Move", command=lambda i=i: doMove(i))
    moveBtn.grid(row=i, column=6)
    moveBtns.append(moveBtn)
    deleteBtn = ttk.Button(sframe, text="Delete", command=lambda i=i: doDelete(i))
    deleteBtn.grid(row=i, column=7)
    deleteBtns.append(deleteBtn)
    replaceBtn = ttk.Button(sframe, text="Replace", command=lambda i=i: doReplace(i))
    replaceBtn.grid(row=i, column=8)
    replaceBtns.append(replaceBtn)
    

frame.pack(fill="both", expand=True)
root.mainloop()
print('exit')