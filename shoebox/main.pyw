# shoebox.main

import os
from tkinter import *
from tkinter import ttk
from shoebox import services
from shoebox.medit import Medit
from shoebox.px import Px

root = Tk()
root.title("Shoebox")
lab = ttk.Label(root, text="Shoebox Launcher")
lab.pack(side=TOP, expand=True, ipady=10)

def launch_px():
    Px()
pxButton = ttk.Button(root, text="Px", command=launch_px)
pxButton.pack(side=LEFT, fill=X, expand=True)

def launch_medit():
    Medit()
meditButton = ttk.Button(root, text="Medit", command=launch_medit)
meditButton.pack(side=LEFT, fill=X, expand=True)

def close_all():
    for px in services.get_pxs():
        px.destroy()
    for medit in services.get_medits():
        medit.destroy()
closeAllButton = ttk.Button(root, text="Close All", command=close_all)
closeAllButton.pack(side=LEFT, fill=X, expand=True)

def on_exit():
    root.destroy()
root.protocol("WM_DELETE_WINDOW", on_exit)

root.mainloop()
