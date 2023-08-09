# copy_files_rename_dups

import sys, os, shutil, re
from tkinter import *
from tkinter import filedialog, messagebox

picturesDir="D:\\Users\\Msaus\\Pictures"
root = Tk()

srcDir = filedialog.askdirectory(title='Select source directory', initialdir=picturesDir)
if not srcDir:
    sys.exit(0)
destDir = filedialog.askdirectory(title='Select destination directory', initialdir=picturesDir)
if not destDir:
    sys.exit(0)

nCopied = 0
nRenamed = 0
nSkipped = 0

def find_unused_name(path):
    head, tail = os.path.split(path)
    name, ext = os.path.splitext(tail)
    mr = re.fullmatch(r'(.*)\((\d+)\)', name)
    if mr:
        name = mr.group(1)
        n = int(mr.group(2)) + 1
    else:
        n = 1
    while True:
        newName = "{}({}){}".format(name, n, ext)
        newPath = os.path.join(head, newName)
        if not os.path.exists(newPath):
            break
        n += 1
    return newName

def copy_files(srcDir, destDir):
    global nCopied, nRenamed, nSkipped
    print("Copying", srcDir, "to", destDir)
    for item in os.listdir(srcDir):
        srcPath = os.path.join(srcDir, item)
        if os.path.isdir(srcPath):
            print("Skipping directory", item)
        else:
            destPath = os.path.join(destDir, item)
            if os.path.exists(destPath):
                if os.path.getsize(srcPath) == os.path.getsize(destPath):
                    print("Skipping", item, "same size")
                    destPath = None
                    nSkipped += 1
                else:
                    newName = find_unused_name(destPath)
                    print("Copying", item, "to", newName)
                    destPath = os.path.join(destDir, newName)
                    nRenamed += 1
            else:
                print("Copying", item)
            if destPath is not None:
                shutil.copyfile(srcPath, destPath)
                nCopied += 1

copy_files(srcDir, destDir)
messagebox.showinfo("Done", "{} copied, {} renamed, {} skipped".format(nCopied, nRenamed, nSkipped))
