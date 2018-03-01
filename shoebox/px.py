# shoebox.px

import os
from tkinter import *
from tkinter import ttk
from PIL import Image
import ImageTk
from shoebox import pic, nailcache
from shoebox.nailer import Nailer
from shoebox.pxfolder import PxFolder
from shoebox.pxtile import PxTilePic, PxTileFile
from tkit.loghelper import LogHelper
from tkit.widgethelper import WidgetHelper

instances = []
nextInstNum = 1

tileGap = 14

class Px(LogHelper, WidgetHelper):
    def __init__(self):
        self.env = {}
        LogHelper.__init__(self, self.env)
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1

        # create top level window
        self.top = Toplevel()
        self.top.title("Px {:d}".format(self.instNum))
        self.top.bind('<Destroy>', self.on_destroy)

        # create top button bar
        self.topBar = Frame(self.top)
        self.topBar.grid(column=0, row=0, sticky=(N,W,E))
        self.refreshButton = ttk.Button(self.topBar, text="Refresh", command=self.do_refresh)
        self.refreshButton.pack(side=LEFT)
        self.sizeButton = ttk.Button(self.topBar, text="Small", command=self.do_size)
        self.sizeButton.pack(side=LEFT)
        self.nailerButton = ttk.Button(self.topBar, text="Nailer", command=self.do_nailer)
        self.nailerButton.pack(side=RIGHT)
        self.enable_buttons(False)

        # create status bar
        self.statusBar = Frame(self.top)
        self.statusBar.grid(column=0, row=1, sticky=(N,W,E))
        self.statusLabel = ttk.Label(self.statusBar, text="")
        self.statusLabel.pack(side=LEFT, fill=X, expand=True)
        self.logButton = ttk.Button(self.statusBar, text="Log", command=self.do_log)
        self.logButton.pack(side=RIGHT)

        # created paned window for tree and canvas
        self.panedWin = PanedWindow(self.top, orient=HORIZONTAL, width=800, height=800, sashwidth=5, sashrelief=GROOVE)
        self.panedWin.grid(column=0, row=2, sticky=(N,W,E,S))
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(2, weight=1)

        # turn off border for all Treeviews.. see https://www.codeday.top/2017/10/26/52272.html
        s = ttk.Style()
        s.layout('Treeview', [('Treeview.field', {'border': 0})])
        # style for error messages (status bar)
        s.configure('Error.TLabel', foreground='red')

        # create tree view for directories
        self.treeFrame = Frame(self.panedWin)
        self.treeScroll = Scrollbar(self.treeFrame)
        self.treeScroll.pack(side=RIGHT, fill=Y)
        self.tree = ttk.Treeview(self.treeFrame, show='tree')
        self.tree.pack(side=RIGHT, fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.configure(yscrollcommand=self.treeScroll.set)
        self.treeScroll.configure(command=self.tree.yview)
        self.panedWin.add(self.treeFrame)

        # tree stuff
        self.tree.tag_configure('noncanon', background='cyan')
        self.tree.tag_configure('error', background='orange')
        self.tree.tag_configure('childerror', background='tan')
        self.treeItems = {}

        # create canvas for tiles
        self.canvasFrame = Frame(self.panedWin)
        self.canvasScroll = Scrollbar(self.canvasFrame)
        self.canvasScroll.pack(side=RIGHT, fill=Y)
        self.canvas = Canvas(self.canvasFrame, scrollregion=(0, 0, 1, 1))
        self.canvas.pack(side=RIGHT, fill=BOTH, expand=True)
        self.canvas.configure(yscrollcommand=self.canvasScroll.set)
        self.canvasScroll.configure(command=self.canvas.yview)
        self.setup_canvas_mousewheel(self.canvas)
        self.panedWin.add(self.canvasFrame)

        # canvas stuff
        self.nailSz = pic.nailSizes[-1]
        self.tiles = []
        self.selectedTiles = []
        self.lastClickIndex = 0
        self.canvasItems = {} #canvas id of image to tile object
        self.canvasWidth = 0
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        self.canvas.bind('<Button>', self.on_canvas_click)

        self.lastError = ""
        self.curFolder = None
        self.nails = None
        self.nailsTried = False
        self.loaded = False
        self.nPictures = 0
        self.rootFolder = PxFolder(None, "", ".", "")
        self.folders = {"": self.rootFolder}
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

    # show error/warning message in status and log it
    # for info and other log messages just log them
    def log_error(self, msg):
        self.lastError = msg
        self.set_status(msg, True)
        super().log_error(msg)

    def log_warning(self, msg):
        self.lastError = msg
        self.set_status(msg, True)
        super().log_warning(msg)

    # when Refresh button clicked
    def do_refresh(self):
        self.clear_canvas()
        self.populate_canvas()

    # when Small/Large button clicked
    def do_size(self):
        i = pic.nailSizes.index(self.nailSz)
        i = (i + 1) % len(pic.nailSizes)
        self.nailSz = pic.nailSizes[i]
        i = (i + 1) % len(pic.nailSizes)
        self.sizeButton.configure(text=pic.nailSizeNames[i])
        self.do_refresh()

    # when Nailer button clicked
    def do_nailer(self):
        if self.curFolder is None:
            Nailer(".")
        else:
            Nailer(self.curFolder.path)

    # when Log button clicked
    def do_log(self):
        self.open_log_window("Log - Px {:d}".format(self.instNum))

    # enable/disable buttons
    def enable_buttons(self, enable=True):
        self.enable_widget(self.refreshButton, enable)
        self.enable_widget(self.sizeButton, enable)
        self.enable_widget(self.nailerButton, enable)

    # populate tree
    def populate_tree(self, parent):
        # note i'm not sorting, on my system scandir returns them sorted already
        for ent in os.scandir(parent.path):
            if ent.is_dir():
                iid = self.tree.insert(parent.iid, 'end', text=ent.name)
                folder = PxFolder(parent, ent.name, ent.path, iid, env=self.env)
                parent.add_child(folder)
                self.treeItems[iid] = folder
                self.add_folder(folder)
                self.populate_tree(folder)

    # add a folder, check for errors
    def add_folder(self, folder):
        if folder.noncanon:
            # folder is noncanonical, ID cannot be parsed
            self.tree.item(folder.iid, tags='noncanon')
        elif folder.id in self.folders:
            # duplicate folder ID
            self.set_folder_error(folder, pic.DUP)
            self.log_error("Duplicate folder ID: {}".format(folder.path))
            otherFolder = self.folders[folder.id]
            if not otherFolder.is_error(pic.DUP):
                self.set_folder_error(otherFolder, pic.DUP)
                self.log_error("Duplicate folder ID: {}".format(otherFolder.path))
        else:
            # folder ID is good, add to collection
            self.folders[folder.id] = folder
            # verify folder ID correctly predicts the folder's place in the tree
            parentId = pic.make_parent_id(folder.parts)
            if parentId not in self.folders or folder.parent is not self.folders[parentId]:
                self.set_folder_error(folder, pic.OOP)
                self.log_error("Folder out of place: {}".format(folder.path))

    # set folder error
    def set_folder_error(self, folder, errBit):
        folder.set_error(errBit)
        self.tree.item(folder.iid, tags='error')
        parent = folder.parent
        while parent and parent.iid and not parent.errors:
            self.tree.item(parent.iid, tags='childerror')
            parent = parent.parent

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
        if not self.loaded:
            self.clear_canvas()
            self.canvas.create_line(0, 0, self.canvasWidth, self.tree.winfo_height())

    # when user clicks in canvas
    def on_canvas_click(self, event):
        items = self.canvas.find_withtag(CURRENT)
        if len(items) and items[0] in self.canvasItems:
            tile = self.canvasItems[items[0]]
            index = self.tiles.index(tile)
            if event.state & 1: #shift
                # extend selection from last clicked tile (not inclusive) to clicked time (inclusive)
                if index < self.lastClickIndex:
                    for i in range(index, self.lastClickIndex):
                        self.select_tile(self.tiles[i])
                else:
                    for i in range(self.lastClickIndex+1, index+1):
                        self.select_tile(self.tiles[i])
            elif event.state & 4: #control
                # toggle selection of clicked tile
                if not tile.selected:
                    self.select_tile(tile)
                else:
                    self.unselect_tile(tile)
            else:
                # plain click, clear all selections and select the clicked tile
                self.unselect_all()
                self.select_tile(tile)
            # remember index of last tile clicked (for shift-click extension)
            self.lastClickIndex = index
        else:
            # clicking outside any tile clears all selections
            self.unselect_all()

    # select a tile
    def select_tile(self, tile):
        if not tile.selected:
            tile.draw_selected(self.canvas)
            self.selectedTiles.append(tile)

    # unselect a tile
    def unselect_tile(self, tile):
        if tile.selected:
            tile.erase_selected(self.canvas)
            self.selectedTiles.remove(tile)

    # unselect all tiles
    def unselect_all(self):
        for tile in self.selectedTiles:
            tile.erase_selected(self.canvas)
        self.selectedTiles = []

    # delete all items in canvas
    def clear_canvas(self):
        self.canvas.delete(ALL)
        self.canvasItems = {}
        self.tiles = []
        self.selectedTiles = []
        self.lastClickIndex = 0

    # add tiles for all pictures in current folder to canvas
    def populate_canvas(self):
        if self.curFolder:
            self.canvas.configure(background="black")
            self.clear_error()
            self.set_status("Loading...")
            self.nPictures = 0
            self.nails = None
            self.nailsTried = False
            x = tileGap / 2
            y = tileGap / 2
            hmax = 0

            # note i'm not sorting, on my system scandir returns them sorted already
            for ent in os.scandir(self.curFolder.path):
                if ent.is_file() and ent.name != "Thumbs.db":
                    if os.path.splitext(ent.name)[1].lower() in pic.pictureExts:
                        self.nPictures += 1
                        tile = self.make_pic_tile(ent)
                    else:
                        tile = self.make_file_tile(ent)

                    tile.add_to_canvas(self.canvas, x, y, self.nailSz)
                    self.add_tile(tile)
                    if tile.h > hmax:
                        hmax = tile.h

                    # bump start position for next tile,
                    # possibly bump to next row
                    x += self.nailSz + tileGap
                    if x + self.nailSz > self.canvasWidth:
                        x = tileGap / 2
                        y += hmax + tileGap
                        hmax = 0
            # bump to next row if partial row
            if x > tileGap:
                y += hmax + tileGap
            # set scroll region to final height
            self.canvas.configure(scrollregion=(0, 0, 1, y))
            # scroll to top
            self.canvas.yview_moveto(0)
            self.set_status_default_or_error()
            self.loaded = True
            self.enable_buttons()

    # make tile for a picture
    def make_pic_tile(self, ent):
        photo = None
        # try to get thumbnails if we haven't already tried
        if self.nails is None and not self.nailsTried:
            self.nailsTried = True
            try:
                self.nails = nailcache.get_nails(self.curFolder.path, self.nailSz, self.env)
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
            return self.make_file_tile(ent)
        else:
            return PxTilePic(ent.name, photo, self.env)

    # make tile for a file
    def make_file_tile(self, ent):
        return PxTileFile(ent.name, self.env)

    # add a tile
    def add_tile(self, tile):
        self.tiles.append(tile)
        self.canvasItems[tile.items[0]] = tile
