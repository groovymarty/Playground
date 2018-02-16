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
        self.top.geometry("800x150")
        self.top.title("Nailer {}".format(self.instNum))
        self.top.bind('<Destroy>', self.on_destroy)
        instances.append(self)

        self.garden = WidgetGarden()
        self.garden.labelText = {'path': "Starting Path", 'recursive': "Recursive"}
        self.garden.begin_layout(self.top, 3)
        self.top.grid_columnconfigure(1, weight=1)
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
        self.garden.next_row()
        self.garden.grid_widget(ttk.Label(self.garden.curParent, text="Doing folder"))
        self.garden.next_col()
        self.curFolderLabel = ttk.Label(self.garden.curParent)
        self.garden.grid_widget(self.curFolderLabel)
        self.garden.next_row()
        self.garden.grid_widget(ttk.Label(self.garden.curParent, text="Doing picture"))
        self.garden.next_col()
        self.curPictureLabel = ttk.Label(self.garden.curParent)
        self.garden.grid_widget(self.curPictureLabel)
        self.garden.next_row()
        self.garden.next_col()
        self.stopButton = ttk.Button(self.garden.curParent, text="Stop", command=self.do_stop)
        self.garden.grid_widget(self.stopButton)
        self.garden.disable_widget(self.stopButton)
        self.garden.end_layout()

        self.absPath = os.path.abspath(path)
        self.garden.write_var('path', self.absPath)
        self.recursive = True
        self.garden.write_var('recursive', self.recursive)
        self.foldersToScan = None
        self.curScan = None
        self.curFolder = ""
        self.quit = False

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
        self.disable_widgets()
        self.absPath = self.garden.read_var('path')
        self.recursive = self.garden.read_var('recursive')
        self.foldersToScan = [self.absPath]
        self.curFolder = None
        self.curScan = None
        self.quit = False
        self.top.after_idle(self.do_next)

    # do the next thing to do
    def do_next(self):
        # possibly quit
        if self.quit:
            self.do_end()
            return
        # possibly advance to next folder
        if self.curScan is None:
            if len(self.foldersToScan):
                self.curFolder = self.foldersToScan.pop()
                self.curFolderLabel.configure(text=self.curFolder)
                self.curScan = os.scandir(self.curFolder)
            else:
                self.do_end()
                return
        # get next entry in current folder scan
        ent = next(self.curScan, None)
        if ent is None:
            self.curScan = None
        elif ent.is_dir():
            if self.recursive:
               self.foldersToScan.append(ent.path)
        else:
            self.curPictureLabel.configure(text=ent.name)

        # that's all for now, come back soon
        self.top.after_idle(self.do_next)

    # when nothing more to do (or quitting because stop button clicked)
    def do_end(self):
        self.curScan = None
        self.foldersToScan = None
        self.curFolderLabel.configure(text="Stopped" if self.quit else "Complete")
        self.curPictureLabel.configure(text="")
        self.disable_widgets(False)

    # when stop button clicked
    def do_stop(self):
        self.quit = True

    # disable most widgets during scan (or enable them afterward)
    def disable_widgets(self, disable=True):
        self.garden.set_widget_disable('path', disable)
        self.garden.set_widget_disable('recursive', disable)
        self.garden.disable_widget(self.pathButton, disable)
        self.garden.disable_widget(self.startButton, disable)
        self.garden.disable_widget(self.stopButton, not disable)
