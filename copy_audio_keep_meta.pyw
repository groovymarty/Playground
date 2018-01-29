# copy_audio_keep_meta

import sys, os, shutil, tkinter
from tkinter import filedialog, messagebox
from mutagen.mp4 import MP4

musicDir="C:\\Users\\Msaus\\Music\\iTunes\\iTunes Media\\Music"
#root = tkinter.Tk()

while True:
    srcFiles = sorted(filedialog.askopenfilenames(title='Select source files', defaultextension='m4a', initialdir=musicDir))
    if not srcFiles:
        sys.exit(0)
    destFiles = sorted(filedialog.askopenfilenames(title='Select destination files', defaultextension='m4a', initialdir=musicDir))
    if not destFiles:
        sys.exit(0)
    if len(srcFiles) != len(destFiles):
        messagebox.showerror("Not same number of files", "Please select the same number of files")
    else:
        break

pairs = list(zip(srcFiles, destFiles))
msg = "Ready to copy:\n\n"
for p in pairs:
    msg += os.path.basename(p[0])+" --> "+os.path.basename(p[1])+"\n"

if not messagebox.askokcancel("Confirm", msg):
    sys.exit(0)

for p in pairs:
    (srcFile, destFile) = p
    meta = MP4(destFile)
    #srcMeta = MP4(srcFile)
    shutil.copyfile(srcFile, destFile)
    #meta.info.length = srcMeta.info.length
    #messagebox.showinfo("Length", srcMeta.info.length)
    meta.save(destFile)

messagebox.showinfo("Done", "Copy complete")

    
