# shoebox.px

import os
from tkinter import *
from tkinter import ttk
from PIL import Image
import ImageTk
from shoebox.nailer import Nailer
from shoebox import pic, nails
from tkit.loghelper import LogHelper

instances = []
nextInstNum = 1

class Px(LogHelper):
    def __init__(self):
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1
        self.top = Toplevel()
        self.top.title("Px {}".format(self.instNum))
        self.top.bind('<Destroy>', self.on_destroy)

        self.topBar = Frame(self.top)
        self.topBar.grid(column=0, row=0, sticky=(N,W))
        self.refreshButton = ttk.Button(self.topBar, text="Refresh", command=self.do_refresh)
        self.refreshButton.pack(side=LEFT)
        self.nailerButton = ttk.Button(self.topBar, text="Nailer", command=self.do_nailer)
        self.nailerButton.pack(side=LEFT)

        self.statusLabel = ttk.Label(self.top, text="")
        self.statusLabel.grid(column=0, row=1, sticky=(N,W,E))

        self.panedWin = PanedWindow(self.top, orient=HORIZONTAL, width=800, height=800, sashwidth=5, sashrelief=GROOVE)
        self.panedWin.grid(column=0, row=2, sticky=(N,W,E,S))
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(2, weight=1)

        # turn off border for all Treeviews.. see https://www.codeday.top/2017/10/26/52272.html
        s = ttk.Style()
        s.layout('Treeview', [('Treeview.field', {'border': 0})])

        self.treeFrame = Frame(self.panedWin)
        self.treeScroll = Scrollbar(self.treeFrame)
        self.treeScroll.pack(side=RIGHT, fill=Y)
        self.tree = ttk.Treeview(self.treeFrame, show='tree')
        self.tree.pack(side=RIGHT, fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.configure(yscrollcommand=self.treeScroll.set)
        self.treeScroll.configure(command=self.tree.yview)
        self.panedWin.add(self.treeFrame)

        self.treeItems = {}
        self.photos = []

        self.canvasFrame = Frame(self.panedWin)
        self.canvasScroll = Scrollbar(self.canvasFrame)
        self.canvasScroll.pack(side=RIGHT, fill=Y)
        self.canvas = Canvas(self.canvasFrame, scrollregion=(0, 0, 1000, 1000))
        self.canvas.pack(side=RIGHT, fill=BOTH, expand=True)
        self.canvas.configure(yscrollcommand=self.canvasScroll.set)
        self.canvasScroll.configure(command=self.canvas.yview)
        self.panedWin.add(self.canvasFrame)

        self.canvas.create_line(0,0,300,1000)
        self.nailSz = pic.nailSizes[-1]
        self.tileGap = 15
        self.x = 0
        self.y = 0
        self.photos = []
        self.canvasWidth = self.canvas.winfo_width()
        self.canvas.bind('<Configure>', self.on_canvas_resize)

        self.curFolder = None
        self.nailIndx = None
        self.nailBuf = None
        self.nPictures = 0
        self.populate_tree("", ".")
        self.set_status_default()
        instances.append(self)

    # called when my top-level window is closed
    # this is the easiest and most common way to destroy Px,
    # and includes the case where the entire shoebox application is shut down
    def on_destroy(self, ev):
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
    def set_status(self, msg):
        self.statusLabel.configure(text=msg)
        self.top.update_idletasks()

    # set status to default message
    def set_status_default(self):
        if self.curFolder is None:
            self.set_status("Select a folder")
        else:
            self.set_status("Ready ({:d} pictures)".format(self.nPictures))

    # when Refresh button clicked
    def do_refresh(self):
        self.clear_canvas()
        self.populate_canvas()

    # when Nailer button clicked
    def do_nailer(self):
        if self.curFolder is None:
            Nailer(".")
        else:
            Nailer(self.curFolder)

    # populate tree
    def populate_tree(self, parent, path):
        for ent in os.scandir(path):
            if ent.is_dir():
                iid = self.tree.insert(parent, 'end', text=ent.name)
                self.treeItems[iid] = ent
                self.populate_tree(iid, ent.path)

    # when user clicks tree item
    def on_tree_select(self, event):
        sel = self.tree.selection()
        if sel:
            ent = self.treeItems[sel[0]]
            if ent:
                self.curFolder = ent.path
                self.clear_canvas()
                self.populate_canvas()

    # when user resizes the window
    def on_canvas_resize(self, event):
        if self.canvas.winfo_width() != self.canvasWidth:
            self.canvasWidth = self.canvas.winfo_width()

    # delete all items in canvas and reset state variables
    def clear_canvas(self):
        self.canvas.addtag_all('xx')
        self.canvas.delete('xx')
        self.x = 0
        self.y = 0
        self.photos = []

    # add tiles for all pictures in current folder to canvas
    def populate_canvas(self):
        if self.curFolder is not None:
            self.set_status("Loading...")
            self.nPictures = 0
            error = False
            try:
                (self.nailIndx, self.nailBuf) = nails.read_nails(self.curFolder, self.nailSz)
            except FileNotFoundError:
                self.set_status("No thumbnail file for size {}".format(self.nailSz))
                error = True
                self.nailIndx = None
                self.nailBuf = None

            for ent in os.scandir(self.curFolder):
                if ent.is_file() and os.path.splitext(ent.name)[1].lower() in pic.pictureExts:
                    self.nPictures += 1
                    self.add_tile(ent)
            if self.x != 0:
                self.y += self.nailSz + self.tileGap
            self.canvas.configure(scrollregion=(0, 0, 1000, self.y))
            if not error:
                self.set_status_default()

    # add a tile for specified directory entry
    def add_tile(self, ent):
        print("adding tile for {}".format(ent.name))
        if self.nailIndx is not None and ent.name in self.nailIndx:
            #TODO: more error handling......
            (offset, length) = self.nailIndx[ent.name]
            data = self.nailBuf[offset : offset+length]
            photo = PhotoImage(format="png", data=data)
        else:
            im = Image.open(ent.path)
            im = pic.fix_image_orientation(im)
            im.thumbnail((self.nailSz, self.nailSz))
            photo = ImageTk.PhotoImage(im)
        self.photos.append(photo)
        self.canvas.create_image(self.x, self.y, image=photo, anchor=NW)
        self.x += self.nailSz + self.tileGap
        if self.x + self.nailSz > self.canvasWidth:
            self.x = 0
            self.y += self.nailSz + self.tileGap
