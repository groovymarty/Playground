# remove_dups

import sys, os, shutil, re
from tkinter import *
from tkinter import filedialog, messagebox

picturesDir="D:\\Users\\Msaus\\Pictures"
root = Tk()

dir = filedialog.askdirectory(title='Select directory', initialdir=picturesDir)
if not dir:
    sys.exit(0)

nRemoved = 0

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

def remove_dups(dir):
    global nRemoved
    print("Scanning", dir)
    for item in os.listdir(dir):
        path = os.path.join(dir, item)
        if os.path.isdir(path):
            print("Skipping directory", item)
        else:
            name, ext = os.path.splitext(item)
            mr = re.fullmatch(r'(.*)\((\d+)\)', name)
            if mr:
                origName = mr.group(1) + ext
                origPath = os.path.join(dir, origName)
                if os.path.exists(origPath) and os.path.getsize(origPath) == os.path.getsize(path):
                    print("Removing", item)
                    os.remove(path)
                    nRemoved += 1

remove_dups(dir)
messagebox.showinfo("Done", "{} removed".format(nRemoved))
