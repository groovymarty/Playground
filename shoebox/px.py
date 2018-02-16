# shoebox.px

import os
from tkinter import *
from tkinter import ttk
from PIL import Image
import ImageTk

instances = []
nextInstNum = 1

class Px:
    def __init__(self):
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1
        self.top = Toplevel()
        self.top.title("Px {}".format(self.instNum))
        self.top.bind('<Destroy>', self.on_destroy)

        self.panedWin = PanedWindow(self.top, orient=HORIZONTAL, width=800, height=800, sashwidth=5, sashrelief=GROOVE)
        self.panedWin.pack(fill=BOTH, expand=True)

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
        self.imgSz = (244, 244)
        self.tileGap = 15
        self.x = 0
        self.y = 0
        self.canvasWidth = self.canvas.winfo_width()
        self.canvas.bind('<Configure>', self.on_canvas_resize)

        self.populate_tree("", ".")
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
                self.clear_canvas()
                self.populate_canvas(ent.path)

    def on_canvas_resize(self, event):
        if self.canvas.winfo_width() != self.canvasWidth:
            self.canvasWidth = self.canvas.winfo_width()

    def clear_canvas(self):
        self.canvas.addtag_all('xx')
        self.canvas.delete('xx')
        self.x = 0
        self.y = 0

    def populate_canvas(self, path):
        for ent in os.scandir(path):
            if ent.is_file():
                self.add_tile(ent)
        if self.x != 0:
            self.y += self.imgSz[1] + self.tileGap
        self.canvas.configure(scrollregion=(0, 0, 1000, self.y))

    def add_tile(self, ent):
        ext = os.path.splitext(ent.name)[1]
        if ext.lower() == ".jpg":
            print("adding tile for {}".format(ent.name))
            im = Image.open(ent.path)
            im.thumbnail(self.imgSz)
            photo = ImageTk.PhotoImage(im)
            self.photos.append(photo)
            self.canvas.create_image(self.x, self.y, image=photo, anchor=NW)
            self.x += self.imgSz[0] + self.tileGap
            if self.x + self.imgSz[0] > self.canvasWidth:
                self.x = 0
                self.y += self.imgSz[1] + self.tileGap
