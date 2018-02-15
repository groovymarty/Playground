# shoebox.nailer

import os
from tkinter import *
from tkinter import ttk, filedialog
from tkit.widgetgarden import WidgetGarden

instances = []
nextInstNum = 1

class Nailer:
    def __init__(self, path):
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1
        self.top = Toplevel()
        self.top.geometry("500x100")
        self.top.title("Nailer {}".format(self.instNum))
        self.top.bind('<Destroy>', self.on_destroy)
        instances.append(self)

        self.garden = WidgetGarden()
        self.garden.labelText = {'path': "Starting Path", 'recursive': "Recursive"}
        self.garden.begin_layout(self.top, 3)
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_columnconfigure(1, weight=10)
        self.garden.make_entry('path')
        self.pathButton = ttk.Button(self.garden.curParent, text="Browse", command=self.do_browse_path)
        self.garden.grid_widget(self.pathButton)
        self.garden.next_row()
        self.garden.next_col()
        self.garden.make_checkbutton('recursive')
        self.garden.next_row()
        self.garden.next_col()
        self.startButton = ttk.Button(self.garden.curParent, text="Start", command=self.do_start)
        self.garden.grid_widget(self.startButton)
        self.garden.end_layout()

        self.absPath = os.path.abspath(path)
        self.garden.write_var('path', self.absPath)
        self.garden.write_var('recursive', True)

    # called when my top-level window is closed
    # this is the easiest and most common way to destroy Nailer,
    # and includes the case where the entire shoebox application is shut down
    def on_destroy(self, ev):
        self.top = None
        self.destroy()

    # destroy and clean up this Nailer
    # in Python you don't really destroy objects, you just remove all references to them
    # so this function removes all known references then closes the top level window
    # note this will result in a second call from the on_destroy event handler; that's ok
    def destroy(self):
        if self in instances:
            instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    # Nailer destructor
    # it's likely destroy() has already been called, but call again just to be sure
    def __del__(self):
        self.destroy()

    # when browse button is clicked
    def do_browse_path(self):
        newDir = filedialog.askdirectory(title="Nailer {} - Select Starting Path".format(self.instNum),
                                         initialdir=self.absPath)
        if newDir:
            self.absPath = newDir
            self.garden.write_var('path', self.absPath)

    # when start button is clicked
    def do_start(self):
        self.garden.set_widget_disable('path')
        self.garden.set_widget_disable('recursive')
        self.garden.disable_widget(self.pathButton)
        self.garden.disable_widget(self.startButton)
        print("you clicked start")
