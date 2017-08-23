# compile_contents

import sys, os, shutil, json
from tkinter import *
from tkinter import filedialog, messagebox

picturesDir="C:\\Users\\Marty\\Pictures"
root = Tk()

compileDir = filedialog.askdirectory(title="Select directory to compile", initialdir=os.path.join(picturesDir, "C01 Slide Shows"))
if not compileDir:
    sys.exit(0)

contentsFile = os.path.join(compileDir, "contents.json")
contents = {}

try:
    with open(contentsFile, mode='r', encoding='UTF-8') as f:
        contents = json.load(f)
except FileNotFoundError as e:
    pass

if 'pictures' not in contents:
    contents['pictures'] = []

nAdded = 0
nAlready = 0
nDeleted = 0

for item in os.listdir(compileDir):
    name, ext = os.path.splitext(item)
    ext = ext.lower()
    if ext == ".jpg" or ext == ".jpeg":
        if name not in contents['pictures']:
            contents['pictures'].append(name)
            nAdded += 1
        else:
            nAlready += 1
        os.remove(os.path.join(compileDir, item))
        nDeleted += 1


with open(contentsFile, mode='w', encoding='UTF-8') as f:
    json.dump(contents, f, indent=2)

messagebox.showinfo("Done", "{} pictures added\n{} pictures already there\n{} files deleted".format(nAdded, nAlready, nDeleted))
