# shoebox.medit

import os
import tkinter as tk
from tkinter import ttk

instances = []
nextInstNum = 1

class Medit:
    def __init__(self):
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1
        self.top = tk.Toplevel()
        self.top.title("Medit {:d}".format(self.instNum))
        self.top.bind('<Destroy>', self.on_destroy)
        instances.append(self)

    # called when my top-level window is closed
    # this is the easiest and most common way to destroy Medit,
    # and includes the case where the entire shoebox application is shut down
    def on_destroy(self, ev):
        self.top = None
        self.destroy()

    # destroy and clean up this Medit
    # in Python you don't really destroy objects, you just remove all references to them
    # so this function removes all known references then closes the top level window
    # note this will result in a second call from the on_destroy event handler; that's ok
    def destroy(self):
        if self in instances:
            instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    # Medit destructor
    # it's likely destroy() has already been called, but call again just to be sure
    def __del__(self):
        self.destroy()
