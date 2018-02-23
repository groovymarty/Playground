# shoebox.px

import os
from tkinter import *
from tkinter import ttk
from PIL import Image
import ImageTk
from shoebox import pic, nailcache
from shoebox.nailer import Nailer
from shoebox.pxfolder import PxFolder
from shoebox.pxtile import PxTile
from tkit.loghelper import LogHelper

instances = []
nextInstNum = 1

tileGap = 14

class Px(LogHelper):
    def __init__(self):
        self.env = {}
        LogHelper.__init__(self, self.env)
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1
        self.top = Toplevel()
        self.top.title("Px {:d}".format(self.instNum))
        self.top.bind('<Destroy>', self.on_destroy)

        self.topBar = Frame(self.top)
        self.topBar.grid(column=0, row=0, sticky=(N,W,E))
        self.refreshButton = ttk.Button(self.topBar, text="Refresh", command=self.do_refresh)
        self.refreshButton.pack(side=LEFT)
        self.nailerButton = ttk.Button(self.topBar, text="Nailer", command=self.do_nailer)
        self.nailerButton.pack(side=LEFT)

        self.statusBar = Frame(self.top)
        self.statusBar.grid(column=0, row=1, sticky=(N,W,E))
        self.statusLabel = ttk.Label(self.statusBar, text="")
        self.statusLabel.pack(side=LEFT, fill=X, expand=True)
        self.logButton = ttk.Button(self.statusBar, text="Log", command=self.do_log)
        self.logButton.pack(side=RIGHT)

        self.panedWin = PanedWindow(self.top, orient=HORIZONTAL, width=800, height=800, sashwidth=5, sashrelief=GROOVE)
        self.panedWin.grid(column=0, row=2, sticky=(N,W,E,S))
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(2, weight=1)

        # turn off border for all Treeviews.. see https://www.codeday.top/2017/10/26/52272.html
        s = ttk.Style()
        s.layout('Treeview', [('Treeview.field', {'border': 0})])
        # style for error messages
        s.configure('Error.TLabel', foreground='red')

        self.treeFrame = Frame(self.panedWin)
        self.treeScroll = Scrollbar(self.treeFrame)
        self.treeScroll.pack(side=RIGHT, fill=Y)
        self.tree = ttk.Treeview(self.treeFrame, show='tree')
        self.tree.pack(side=RIGHT, fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.configure(yscrollcommand=self.treeScroll.set)
        self.treeScroll.configure(command=self.tree.yview)
        self.panedWin.add(self.treeFrame)

        self.tree.tag_configure('noncanon', background='lavender')
        self.treeItems = {}

        self.canvasFrame = Frame(self.panedWin)
        self.canvasScroll = Scrollbar(self.canvasFrame)
        self.canvasScroll.pack(side=RIGHT, fill=Y)
        self.canvas = Canvas(self.canvasFrame, scrollregion=(0, 0, 1, 1))
        self.canvas.pack(side=RIGHT, fill=BOTH, expand=True)
        self.canvas.configure(yscrollcommand=self.canvasScroll.set)
        self.canvasScroll.configure(command=self.canvas.yview)
        self.panedWin.add(self.canvasFrame)

        self.nailSz = pic.nailSizes[-1]
        self.x = 0
        self.y = 0
        self.tiles = {}
        self.canvasWidth = 0
        self.canvasBlank = True
        self.canvas.bind('<Configure>', self.on_canvas_resize)

        self.lastError = ""
        self.curFolder = None
        self.nails = None
        self.nailsTried = False
        self.nPictures = 0
        self.rootFolder = PxFolder(None, "", ".", "")
        self.populate_tree(self.rootFolder)
        self.set_status_default_or_error()
        instances.append(self)

    # called when my top-level window is closed
    # this is the easiest and most common way to destroy Px,
    # and includes the case where the entire shoebox application is shut down
    def on_destroy(self, ev):
        LogHelper.__del__(self)
        self.top = None
        self.destroy()

    # destroy and clean up this Px
    # in Python you don't really destroy objects, you just remove all references to them
    # so this function removes all known references then closes the top level window
    # note this will result in a second call from the on_destroy event handler; that's ok
    def destroy(self):
        if self in instances:
            instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    # Px destructor
    # it's likely destroy() has already been called, but call again just to be sure
    def __del__(self):
        self.destroy()

    # set status to specified string
    def set_status(self, msg, error=False):
        self.statusLabel.configure(text=msg, style="Error.TLabel" if error else "TLabel")
        self.top.update_idletasks()

    # set status to default message
    def set_status_default(self):
        if self.curFolder is None:
            self.set_status("Select a folder")
        else:
            self.set_status("Ready ({:d} pictures)".format(self.nPictures))

    # set status to default message or error
    def set_status_default_or_error(self):
        if self.lastError:
            self.set_status("Ready / "+self.lastError, True)
        else:
            self.set_status_default()

    # clear last error
    def clear_error(self):
        self.lastError = ""

    # show info message in status and log it
    def log_info(self, msg):
        self.set_status(msg)
        super().log_info(msg)

    # show error message in status and log it
    def log_error(self, msg):
        self.lastError = msg
        self.set_status(msg, True)
        super().log_error(msg)

    # show warning message in status and log it
    def log_warning(self, msg):
        self.lastError = msg
        self.set_status(msg, True)
        super().log_warning(msg)

    # when Refresh button clicked
    def do_refresh(self):
        self.clear_canvas()
        self.populate_canvas()

    # when Nailer button clicked
    def do_nailer(self):
        if self.curFolder is None:
            Nailer(".")
        else:
            Nailer(self.curFolder.path)

    # when Log button clicked
    def do_log(self):
        self.open_log_window("Log - Px {:d}".format(self.instNum))

    # populate tree
    def populate_tree(self, parent):
        for ent in os.scandir(parent.path):
            if ent.is_dir():
                iid = self.tree.insert(parent.iid, 'end', text=ent.name)
                folder = PxFolder(parent, ent.name, ent.path, iid, env=self.env)
                parent.add_child(folder)
                self.treeItems[iid] = folder
                if folder.noncanon:
                    self.tree.item(iid, tags='noncanon')
                self.populate_tree(folder)

    # when user clicks tree item
    def on_tree_select(self, event):
        sel = self.tree.selection()
        if sel and sel[0] in self.treeItems:
            self.curFolder = self.treeItems[sel[0]]
            self.clear_canvas()
            self.populate_canvas()

    # when user resizes the window
    def on_canvas_resize(self, event):
        if self.canvas.winfo_width() != self.canvasWidth:
            self.canvasWidth = self.canvas.winfo_width()
        if self.canvasBlank:
            self.clear_canvas()
            self.canvas.create_line(0, 0, self.canvasWidth, self.tree.winfo_height())

    # delete all items in canvas and reset state variables
    def clear_canvas(self):
        self.canvas.addtag_all('xx')
        self.canvas.delete('xx')
        self.x = tileGap / 2;
        self.y = tileGap / 2;
        self.tiles = {}

    # add tiles for all pictures in current folder to canvas
    def populate_canvas(self):
        self.canvasBlank = False
        self.canvas.configure(background="black")
        if self.curFolder is not None:
            self.clear_error()
            self.set_status("Loading...")
            self.nPictures = 0
            self.nails = None
            self.nailsTried = False

            for ent in os.scandir(self.curFolder.path):
                if ent.is_file():
                    if os.path.splitext(ent.name)[1].lower() in pic.pictureExts:
                        self.nPictures += 1
                        self.add_pic_tile(ent)
                    else:
                        self.add_file_tile(ent)
                    self.x += self.nailSz + tileGap
                    if self.x + self.nailSz > self.canvasWidth:
                        self.x = tileGap / 2
                        self.y += self.nailSz + tileGap
            if self.x > tileGap:
                self.y += self.nailSz + tileGap
            self.canvas.configure(scrollregion=(0, 0, 1, self.y))
            self.set_status_default_or_error()

    # add tile for a picture
    def add_pic_tile(self, ent):
        photo = None
        # try to get thumbnails if we haven't already tried
        if self.nails is None and not self.nailsTried:
            self.nailsTried = True
            try:
                self.nails = nailcache.get_nails(self.curFolder.path, self.nailSz)
            except FileNotFoundError:
                self.log_error("No thumbnail file for size {}".format(self.nailSz))
            except RuntimeError as e:
                self.log_error(e.message)
        # try to get image from thumbnails
        if self.nails is not None:
            try:
                data = self.nails.get_by_name(ent.name)
                try:
                    photo = PhotoImage(format="png", data=data)
                except:
                    raise RuntimeError("Can't create image from XPNG for {}".format(ent.name))
            except RuntimeError as e:
                self.log_error(str(e))
        # if still no image, try to create thumbnail on the fly
        if photo is None:
            try:
                im = Image.open(ent.path)
                im = pic.fix_image_orientation(im)
                im.thumbnail((self.nailSz, self.nailSz))
                photo = ImageTk.PhotoImage(im)
            except:
                self.log_error("Can't create thumbnail for {}".format(ent.name))
        # if still no image, give up and display as a file
        if photo is None:
            self.add_file_tile(ent)
        else:
            oid = self.canvas.create_image(self.x, self.y, image=photo, anchor=NW)
            self.tiles[oid] = PxTile(photo)

    # add tile for a file
    def add_file_tile(self, ent):
        rectSz = 128
        print(ent.name)
        oid = self.canvas.create_rectangle(self.x, self.y, self.x+rectSz, self.y+rectSz, fill="gray")
        self.canvas.create_line(self.x, self.y, self.x+rectSz, self.y+rectSz)
        self.tiles[oid] = PxTile(None)
