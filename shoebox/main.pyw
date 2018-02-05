# shoebox.main

import os
from tkinter import *
from tkinter import ttk
from shoebox import services
from shoebox.medit import Medit

root = Tk()
root.title("Shoebox")
#root.geometry("750x650")
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

def launch_medit():
    Medit();
meditButton = ttk.Button(root, text="Medit", command=launch_medit)
meditButton.grid(column=0, row=0, sticky=(N, W))

def destroy_medits():
    for medit in services.get_medits():
        medit.destroy()
destroyButton = ttk.Button(root, text="Destroy Medits", command=destroy_medits)
destroyButton.grid(column=1, row=0, sticky=(N, W))

def on_exit():
    root.destroy()
root.protocol("WM_DELETE_WINDOW", on_exit)

root.mainloop()
