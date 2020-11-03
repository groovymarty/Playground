# find_files_by_content

import sys, os, shutil, hashlib
from tkinter import *
from tkinter import filedialog, messagebox

picturesDir="C:\\Users\\Msaus\\Pictures"
root = Tk()

targetFiles = sorted(filedialog.askopenfilenames(title='Select files to find', initialdir=picturesDir))
if not targetFiles:
    sys.exit(0)
searchDir = filedialog.askdirectory(title='Select directory to search', initialdir=picturesDir)
if not searchDir:
    sys.exit(0)

def hash_file(path, blocksize=65536):
    hasher=hashlib.md5()
    with open(path, mode="rb") as file:
        buf = file.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = file.read(blocksize)
    return hasher.digest()

targetSizes = [os.path.getsize(file) for file in targetFiles]
targetHashes = [hash_file(file) for file in targetFiles]
targetFound = {}
matches = []
numHashed = 0

def scan_dir(dir):
    global numHashed
    print("Scanning",dir)
    for item in os.listdir(dir):
        path = os.path.join(dir, item)
        if os.path.isdir(path):
            scan_dir(path)
        else:
            size = os.path.getsize(path)
            sizeMatches = [i for i, targSize in enumerate(targetSizes)
                           if size == targSize and not os.path.samefile(path, targetFiles[i])]
            if sizeMatches:
                hash = hash_file(path)
                numHashed += 1
                hashMatches = [i for i in sizeMatches if hash == targetHashes[i]]
                for i in hashMatches:
                    print("Found",path)
                    targetFound[i] = True
                    matches.append((i, path))

def delete_found():
    for i, matchPath in matches:
        print("deleting", targetFiles[i])
        os.remove(targetFiles[i])

scan_dir(searchDir)
matches.sort()
print(len(matches), "matches found")
print(numHashed, "files hashed")

if matches:
    root.title("Results")
    root.geometry("750x500")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)
    delFoundBtn = Button(root, text="Delete Found", command=delete_found)
    delFoundBtn.grid(row=0, column=0, sticky=(N,W))
    text = Text(root)
    text.grid(row=1, column=0, sticky=(N,S,W,E))
    sb = Scrollbar(root, orient=VERTICAL, command=text.yview)
    sb.grid(row=1, column=1, sticky=(N,S))
    text['yscrollcommand'] = sb.set

    text.insert(END, "Found:\n")
    for i, path in matches:
        text.insert(END, "{} -> {}\n".format(os.path.basename(targetFiles[i]), path))
    text.insert(END, "\n")
    text.insert(END, "Not found:\n")
    for i, targFile in enumerate(targetFiles):
        if not i in targetFound:
            text.insert(END, "{}\n".format(targetFiles[i]))
    root.mainloop()
else:
    messagebox.showinfo("Done", "No matches found.")
