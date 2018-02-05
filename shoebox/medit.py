# shoebox.medit

import os
import tkinter as tk
from tkinter import ttk
from shoebox import services

class Medit:
    def __init__(self):
        self.top = tk.Toplevel()
        self.top.title("Medit")
        #root.geometry("750x650")
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(0, weight=1)
        self.top.bind('<Destroy>', self.on_destroy)
        services.add_medit(self)

    # called when my top-level window is closed
    # this is the easiest and most common way to destroy an Medit,
    # and includes the case where the entire shoebox application is shut down
    def on_destroy(self, ev):
        self.top = None
        self.destroy()

    # destroy and clean up this Medit
    # in Python you don't really destroy objects, you just remove all references to them
    # so this function removes all known references then closes the top level window
    # note this will result in a second call from the on_destroy event handler; that's ok
    def destroy(self):
        services.remove_medit(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    # Medit destructor
    # it's likely destroy() has already been called, but call again just to be sure
    def __del__(self):
        self.destroy()
