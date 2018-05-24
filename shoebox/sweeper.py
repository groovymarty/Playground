# shoebox.sweeper

import os, io
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from tkit.widgetgarden import WidgetGarden
from tkit.direntry import DirEntry
from shoebox import pic, nails, nailcache, metacache
from tkit.loghelper import LogHelper

instances = []
nextInstNum = 1
delayMs = 15

class Folder:
    def __init__(self, ent, parent):
        self.ent = ent
        self.parent = parent
        self.parts = None
        self.noncanon = False

class Sweeper(LogHelper):
    def __init__(self, path):
        self.env = {}
        LogHelper.__init__(self, self.env)
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1
        self.top = Toplevel()
        self.top.geometry("800x200")
        self.top.title("Sweeper {:d}".format(self.instNum))
        self.top.bind('<Destroy>', self.on_destroy)
        instances.append(self)

        self.garden = WidgetGarden()
        self.garden.labelText = {'path': "Starting Path:", 'recursive': "Recursive", 'checkmeta': "Check Meta"}
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
        self.garden.make_checkbutton('checkmeta')
        self.logButton = ttk.Button(self.garden.curParent, text="Log", command=self.do_log)
        self.garden.grid_widget(self.logButton)
        self.garden.next_row()
        self.garden.next_col()
        self.startButton = ttk.Button(self.garden.curParent, text="Start", command=self.do_start)
        self.garden.grid_widget(self.startButton)
        self.garden.next_row()
        self.garden.grid_widget(ttk.Label(self.garden.curParent, text="Doing folder:"))
        self.garden.next_col()
        self.curFolderLabel = ttk.Label(self.garden.curParent)
        self.garden.grid_widget(self.curFolderLabel)
        self.garden.next_row()
        self.garden.grid_widget(ttk.Label(self.garden.curParent, text="Total:"))
        self.garden.next_col()
        self.totalLabel = ttk.Label(self.garden.curParent)
        self.garden.grid_widget(self.totalLabel)
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
        self.checkmeta = False
        self.garden.write_var('checkmeta', self.checkmeta)
        self.foldersToScan = None
        self.curFolder = None
        self.curScan = None
        self.curEnt = None
        self.metaDict = None
        self.deleteList = None
        self.dupIdCheck = None
        self.prevSortNum = 0
        self.quit = False
        self.nFolders = 0
        self.nPictures = 0
        self.nErrors = 0

    def on_destroy(self, ev):
        """called when my top-level window is closed
        this is the easiest and most common way to destroy Sweeper,
        and includes the case where the entire shoebox application is shut down
        """
        self.top = None
        self.destroy()

    def destroy(self):
        """destroy and clean up this Sweeper
        in Python you don't really destroy objects, you just remove all references to them
        so this function removes all known references then closes the top level window
        note this will result in a second call from the on_destroy event handler; that's ok
        """
        self.close_log_windows()
        if self in instances:
            instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    def __del__(self):
        """Sweeper destructor"""
        self.destroy() #probably already called

    def do_browse_path(self):
        """when browse button is clicked"""
        newDir = filedialog.askdirectory(title="Sweeper {} - Select Starting Path".format(self.instNum),
                                         initialdir=self.absPath)
        if newDir:
            self.absPath = newDir
            self.garden.write_var('path', self.absPath)

    def do_log(self):
        """when Log button clicked"""
        self.open_log_window("Log - Sweeper {:d}".format(self.instNum))

    def log_error(self, msg):
        self.nErrors += 1
        super().log_error(msg)

    def get_delay_ms(self):
        """return delay in milliseconds"""
        return delayMs

    def do_start(self):
        """when start button is clicked"""
        self.disable_widgets()
        self.absPath = self.garden.read_var('path')
        self.recursive = self.garden.read_var('recursive')
        self.checkmeta = self.garden.read_var('checkmeta')
        self.foldersToScan = [Folder(DirEntry(self.absPath), None)]
        self.curFolder = None
        self.metaDict = None
        self.deleteList = None
        self.curScan = None
        self.curEnt = None
        self.quit = False
        self.nFolders = 0
        self.nPictures = 0
        self.nErrors = 0
        self.update_totals()
        self.top.after(self.get_delay_ms(), self.do_next)

    def do_stop(self):
        """when stop button clicked"""
        self.quit = True

    def do_next(self):
        """do the next thing to do"""
        # possibly quit
        if self.quit:
            self.do_end()
            return
        # possibly advance to next folder
        if self.curScan is None:
            if len(self.foldersToScan):
                self.curFolder = self.foldersToScan.pop()
                self.curFolderLabel.configure(text=self.curFolder.ent.path)
                self.nFolders += 1
                self.update_totals()
                parts = pic.parse_folder(self.curFolder.ent.name, self.env)
                self.curFolder.parts = parts
                parent = self.curFolder.parent
                self.curFolder.noncanon = not parts or not parts.id or (parent and parent.noncanon)
                self.curScan = os.scandir(self.curFolder.ent.path)
                self.curEnt = None
                self.begin_folder()
            else:
                self.do_end()
                return
        # do all entries in current scan
        while self.curScan:
            ent = next(self.curScan, None)
            if ent is None:
                # scan is done
                self.curScan = None
                self.curEnt = None
                self.finish_folder()
                break
            elif ent.is_dir():
                # is a directory, remember for later if recursive
                if self.recursive:
                   self.foldersToScan.append(Folder(ent, self.curFolder))
            elif os.path.splitext(ent.path)[1].lower() in pic.pictureExts:
                # is a picture
                self.nPictures += 1
                self.update_totals()
                self.curEnt = ent
                self.do_picture()
        # that's all for now, come back soon
        self.top.after(self.get_delay_ms(), self.do_next)

    def update_totals(self):
        """update totals"""
        self.totalLabel.configure(text="{:d} folders, {:d} pictures, {:d} errors".format(
            self.nFolders, self.nPictures, self.nErrors))

    def begin_folder(self):
        """begin processing a folder"""
        self.dupIdCheck = {}
        self.prevSortNum = 0
        if self.checkmeta:
            self.metaDict = metacache.get_meta_dict(self.curFolder.ent.path, self.env, False)
            self.deleteList = []
        pass

    def do_picture(self):
        """process one picture"""
        if not self.curFolder.noncanon:
            parts = pic.parse_file(self.curEnt.name, self.env)
            if parts and parts.id:
                id = parts.id
                error = False
                # check for duplicate ID
                if id in self.dupIdCheck:
                    self.log_error("Duplicate ID: {}".format(self.curEnt.path))
                    error = True
                else:
                    self.dupIdCheck[id] = True
                # verify ID correctly predicts the folder where item can be found
                folderId = pic.get_folder_id(parts)
                if folderId != self.curFolder.parts.id:
                    self.log_error("Picture out of place: {}".format(self.curEnt.path))
                    error = True
                # check for out of order
                if not error:
                    if parts.sortNum > self.prevSortNum:
                        self.prevSortNum = parts.sortNum
                    else:
                        self.log_error("Out of order: {}".format(self.curEnt.path))
                # checking metadata?
                if self.metaDict:
                    rating = self.metaDict.get_rating(id)
                    if rating == 1:
                        self.deleteList.append(self.curEnt.name)

            else:
                self.log_error("Noncanonical: {}".format(self.curEnt.path))

    def finish_folder(self):
        """finish processing a folder"""
        if self.deleteList and len(self.deleteList):
            items = "\n".join(self.deleteList)
            msg = "{:d} items marked for deletion, are you sure you want delete them?\n{}".format(
                len(self.deleteList), items)
            if messagebox.askyesno("Confirm Delete", msg):
                pass

        self.metaDict = None
        self.deleteList = None

    def do_end(self):
        """when nothing more to do (or quitting because stop button clicked)"""
        self.curScan = None
        self.foldersToScan = None
        msg = "Stopped" if self.quit else "Complete"
        self.curFolderLabel.configure(text=msg)
        self.disable_widgets(False)

    def disable_widgets(self, disable=True):
        """disable most widgets during scan (or enable them afterward)"""
        self.garden.set_widget_disable('path', disable)
        self.garden.set_widget_disable('recursive', disable)
        self.garden.set_widget_disable('checkmeta', disable)
        self.garden.disable_widget(self.startButton, disable)
        self.garden.disable_widget(self.stopButton, not disable)
