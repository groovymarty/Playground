# shoebox.px

import os, shutil
from tkinter import *
from tkinter import ttk, messagebox, simpledialog
from PIL import Image
import ImageTk
from shoebox import pic, nails, nailcache, dnd, metacache
from shoebox.dnd import DndItemEnt
from shoebox.nailer import Nailer
from shoebox.sweeper import Sweeper
from shoebox.pxfolder import PxFolder
from shoebox.pxtile import PxTilePic, PxTileFile, PxTileHole, selectColors
from tkit.direntry import DirEntryFile
from tkit.loghelper import LogHelper
from tkit.widgethelper import WidgetHelper
from tkit import tkit

instances = []
nextInstNum = 1

tileGap = 14

def get_instance(instNum=None):
    """return an instance"""
    try:
        return next(inst for inst in instances if inst.instNum == instNum)
    except StopIteration:
        return instances[0] if len(instances) else None

class PxOptionsDialog(simpledialog.Dialog):
    def __init__(self, px):
        self.px = px
        simpledialog.Dialog.__init__(self, px.top, title="Options - {}".format(px.myName))

    def body(self, master):
        master.columnconfigure(1, weight=1)
        Label(master, text="Comment Mode").grid(row=0, sticky=W)
        self.commentMode = ttk.Combobox(master, values=("Discard", "Trim 2", "Keep All"))
        self.commentMode.current(self.px.commentMode)
        self.commentMode.state(['readonly'])
        self.commentMode.grid(row=0, column=1, sticky=W)
        self.numByTensVar = BooleanVar()
        self.numByTensVar.set(self.px.numByTens)
        self.numByTens = ttk.Checkbutton(master, variable=self.numByTensVar, text="Number by tens")
        self.numByTens.grid(row=1, column=1, sticky=W)
        self.reformatEnabVar = BooleanVar()
        self.reformatEnabVar.set(self.px.reformatEnab)
        self.reformatEnab = ttk.Checkbutton(master, variable=self.reformatEnabVar, text="Reformat existing numbers")
        self.reformatEnab.grid(row=2, column=1, sticky=W)

    def apply(self):
        self.px.commentMode = self.commentMode.current()
        self.px.numByTens = self.numByTensVar.get()
        self.px.reformatEnab = self.reformatEnabVar.get()

class PxRenameDialog(simpledialog.Dialog):
    def __init__(self, px, tile):
        self.px = px
        self.tile = tile
        simpledialog.Dialog.__init__(self, px.top, title="Rename - {}".format(px.myName))

    def body(self, master):
        master.columnconfigure(1, weight=1, minsize=500)
        Label(master, text="Old Name:").grid(row=0, sticky=W)
        Label(master, text=self.tile.name).grid(row=0, column=1, sticky=W)
        Label(master, text="New Name:").grid(row=1, sticky=W)
        self.newName = ttk.Entry(master)
        self.newName.grid(row=1, column=1, sticky=(W,E))
        self.newName.insert(0, self.tile.name)

    def apply(self):
        self.px.do_rename_apply(self.tile, self.newName.get())

class PxMetaDialog(simpledialog.Dialog):
    def __init__(self, px, tile):
        self.px = px
        self.tile = tile
        simpledialog.Dialog.__init__(self, px.top, title="Edit Metadata - {}".format(px.myName))

    def body(self, master):
        master.columnconfigure(1, weight=1, minsize=500)
        Label(master, text="Picture ID:").grid(row=0, sticky=W)
        Label(master, text=self.tile.id).grid(row=0, column=1, sticky=W)
        Label(master, text="Rating").grid(row=1, sticky=W)
        self.rating = ttk.Combobox(master, values=list(reversed(pic.ratings)))
        self.rating.current(pic.flip_rating(self.tile.rating))
        self.rating.state(['readonly'])
        self.rating.grid(row=1, column=1, sticky=W)
        Label(master, text="Caption").grid(row=2, sticky=W)
        self.caption = ttk.Entry(master)
        self.caption.grid(row=2, column=1, sticky=(W,E))
        self.caption.insert(0, self.tile.caption)

    def apply(self):
        self.px.get_meta_dict()
        rating = pic.flip_rating(self.rating.current())
        self.tile.set_rating(rating)
        self.px.metaDict.set_rating(self.tile.id, rating)
        caption = self.caption.get()
        self.tile.set_caption(caption)
        self.px.metaDict.set_caption(self.tile.id, caption)
        self.tile.redraw_text(self.px.canvas, self.px.nailSz)
        self.tile.redraw_icon(self.px.canvas)
        self.px.metaDict.write(self.px.env)
        self.px.forget_meta_dict()

class Px(LogHelper, WidgetHelper):
    def __init__(self):
        self.env = {}
        LogHelper.__init__(self, self.env)
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1

        # create top level window
        self.top = Toplevel()
        self.myName = "Px {:d}".format(self.instNum)
        self.styleRoot = "Px{:d}".format(self.instNum)
        self.top.title(self.myName)
        self.top.bind('<Destroy>', self.on_destroy)

        # create top button bar
        self.topBar = Frame(self.top)
        self.topBar.grid(column=0, row=0, sticky=(N,W,E))
        self.refreshButton = ttk.Button(self.topBar, text="Refresh", command=self.do_refresh)
        self.refreshButton.pack(side=LEFT)
        self.sizeButton = ttk.Button(self.topBar, text="Small", command=self.toggle_nail_size)
        self.sizeButton.pack(side=LEFT)
        self.selectButton = ttk.Button(self.topBar, text="Select All", style=self.styleRoot+".Select.TButton",
                                       command=self.toggle_select_all)
        self.selectButton.pack(side=LEFT)
        self.numButton = ttk.Button(self.topBar, text="Num", command=self.do_num)
        self.numButton.pack(side=LEFT)
        self.unnumButton = ttk.Button(self.topBar, text="Unnum", command=self.do_unnum)
        self.unnumButton.pack(side=LEFT)
        self.sortButton = ttk.Button(self.topBar, text="Sort", command=self.do_sort)
        self.sortButton.pack(side=LEFT)
        self.sweeperButton = ttk.Button(self.topBar, text="Sweeper", command=self.do_sweeper)
        self.sweeperButton.pack(side=RIGHT)
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
        self.optionsButton = ttk.Button(self.statusBar, text="Options", command=self.do_options)
        self.optionsButton.pack(side=RIGHT)

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
        # style to show current selection color
        s.configure('Select.TButton', background=selectColors[1])

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
        self.treeItems = {} #tree iid to file object

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
        self.tiles = {} #groovy id to tile object (note only canonical names have ids)
        self.tilesOrder = [] #array of tiles in display order (all tiles whether canononical or not)
        self.tilesByName = {} #name to tile object
        self.lastTileClicked = None
        self.curSelectColor = 1
        self.dragging = False
        self.dragStart = None
        self.dragTiles = None
        self.dragColor = None
        self.dragCopy = False
        self.canvasItems = {} #canvas id of image to tile object
        self.canvasWidth = 0
        self.hTotal = 0
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<Double-Button-1>', self.on_canvas_doubleclick)
        self.canvas.bind('<Button-3>', self.on_canvas_rclick)
        self.canvas.bind('<B1-Motion>', self.on_canvas_dnd_motion)
        self.canvas.bind('<ButtonRelease>', self.on_canvas_dnd_release)
        self.canvas.bind('<Key>', self.on_canvas_key)
        dnd.add_target(self.canvas, self, self.myName)

        # popup menu
        self.popMenu = Menu(self.top, tearoff=0)
        self.popMenu.add_command(label="Rename", command=self.do_rename)
        self.popMenu.add_command(label="Edit Metadata", command=self.do_edit_meta)
        self.popMenu.add_command(label="Delete", command=self.do_delete)
        self.popMenu.add_separator()
        self.popMenu.add_command(label="[X] Close Menu", command=self.do_close_menu)
        self.popMenuTile = None

        self.lastError = ""
        self.curFolder = None
        self.nails = None
        self.nailsTried = False
        self.metaDict = None
        self.metaDictRefCnt = 0
        self.loaded = False
        self.nPictures = 0
        self.numDigits = 0
        self.numByTens = True
        self.reformatEnab = False
        self.commentMode = pic.TRIM2
        self.rootFolder = PxFolder(None, "", ".", "")
        self.folders = {"": self.rootFolder} #folder id to folder object
        self.populate_tree(self.rootFolder)
        self.set_status_default_or_error()
        instances.append(self)

    def on_destroy(self, ev):
        """called when my top-level window is closed
        this is the easiest and most common way to destroy Px,
        and includes the case where the entire shoebox application is shut down
        """
        self.top = None
        self.destroy()

    def destroy(self):
        """destroy and clean up this Px
        in Python you don't really destroy objects, you just remove all references to them
        so this function removes all known references then closes the top level window
        note this will result in a second call from the on_destroy event handler; that's ok
        """
        dnd.remove_target(self.canvas)
        self.close_log_windows()
        if self in instances:
            instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    def __del__(self):
        """Px destructor"""
        self.destroy() #probably already called
        LogHelper.__del__(self)

    def set_status(self, msg, error=False):
        """set status to specified string"""
        self.statusLabel.configure(text=msg, style="Error.TLabel" if error else "TLabel")
        self.top.update_idletasks()

    def set_status_default(self):
        """set status to default message"""
        if self.curFolder is None:
            self.set_status("Select a folder")
        else:
            self.set_status("Ready ({:d} pictures)".format(self.nPictures))

    def set_status_default_or_error(self):
        """set status to default message or error"""
        if self.lastError:
            self.set_status("Ready / "+self.lastError, True)
        else:
            self.set_status_default()

    def clear_error(self):
        """clear last error"""
        self.lastError = ""

    def log_error(self, msg):
        """show error/warning message in status and log it
        for info optionally show in status and log it
        """
        self.lastError = msg
        self.set_status(msg, True)
        super().log_error(msg)

    def log_warning(self, msg):
        self.lastError = msg
        self.set_status(msg, True)
        super().log_warning(msg)

    def log_info(self, msg, showInStatus=False):
        if showInStatus:
            self.set_status(msg)
        super().log_info(msg)

    def do_refresh(self):
        """when Refresh button clicked"""
        selections = self.save_selections()
        self.clear_canvas()
        self.populate_canvas(os.scandir(self.curFolder.path))
        self.apply_selections(selections)

    def toggle_nail_size(self):
        """when Small/Large button clicked"""
        i = pic.nailSizes.index(self.nailSz)
        i = (i + 1) % len(pic.nailSizes)
        self.nailSz = pic.nailSizes[i]
        i = (i + 1) % len(pic.nailSizes)
        self.sizeButton.configure(text=pic.nailSizeNames[i])
        self.do_refresh()

    def toggle_select_all(self):
        """when Select All/Deselect button clicked"""
        if self.any_selected(self.curSelectColor):
            self.select_all(False, self.curSelectColor)
            self.lastTileClicked = None
        elif self.any_selected():
            self.select_all(False)
            self.lastTileClicked = None
        else:
            self.select_all(self.curSelectColor)
        self.update_select_button()
        self.update_select_status()
        # send focus back to canvas
        self.canvas.focus_set()

    def update_select_button(self):
        """update Select All/Deselect button"""
        if self.any_selected(self.curSelectColor):
            self.selectButton.configure(text="Deselect")
        elif self.any_selected():
            self.selectButton.configure(text="Deselect All")
        else:
            self.selectButton.configure(text="Select All")
        s = ttk.Style()
        s.configure(self.styleRoot+'.Select.TButton', background=selectColors[self.curSelectColor])

    def update_select_status(self):
        """update status to say what's selected"""
        self.set_status("{:d} items selected {}".format(self.num_selected(self.curSelectColor),
                                                        selectColors[self.curSelectColor]))

    def do_nailer(self):
        """when Nailer button clicked"""
        if self.curFolder is None:
            Nailer(".")
        else:
            Nailer(self.curFolder.path)

    def do_sweeper(self):
        """when Sweeper button clicked"""
        if self.curFolder is None:
            Sweeper(".")
        else:
            Sweeper(self.curFolder.path)

    def do_log(self):
        """when Log button clicked"""
        self.open_log_window("Log - {}".format(self.myName))

    def do_options(self):
        """when Options button clicked"""
        PxOptionsDialog(self)

    def enable_buttons(self, enable=True):
        """enable/disable buttons"""
        self.enable_widget(self.refreshButton, enable)
        self.enable_widget(self.sizeButton, enable)
        self.enable_widget(self.selectButton, enable)
        self.enable_widget(self.numButton, enable)
        self.enable_widget(self.unnumButton, enable)
        self.enable_widget(self.sortButton, enable)
        self.enable_widget(self.nailerButton, enable)
        self.enable_widget(self.sweeperButton, enable)

    def populate_tree(self, parent):
        """populate tree
        note i'm not sorting, on my system scandir returns them sorted already
        """
        for ent in os.scandir(parent.path):
            if ent.is_dir():
                iid = self.tree.insert(parent.iid, 'end', text=ent.name)
                folder = PxFolder(parent, ent.name, ent.path, iid, env=self.env)
                parent.add_child(folder)
                self.treeItems[iid] = folder
                self.add_folder(folder)
                self.populate_tree(folder)

    def add_folder(self, folder):
        """add a folder, check for errors"""
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
            parentId = pic.get_parent_id(folder.parts)
            if parentId not in self.folders or folder.parent is not self.folders[parentId]:
                self.set_folder_error(folder, pic.OOP)
                self.log_error("Folder out of place: {}".format(folder.path))

    def set_folder_error(self, folder, errBit):
        """set folder error"""
        folder.set_error(errBit)
        self.tree.item(folder.iid, tags='error')
        parent = folder.parent
        while parent and parent.iid and not parent.errors:
            self.tree.item(parent.iid, tags='childerror')
            parent = parent.parent

    def on_tree_select(self, event):
        """when user clicks tree item"""
        sel = self.tree.selection()
        if sel and sel[0] in self.treeItems:
            self.load_folder(self.treeItems[sel[0]])

    def load_folder(self, folder):
        """load specified folder"""
        self.curFolder = folder
        self.top.title("{} - {}".format(self.myName, self.curFolder.path[2:]))
        self.clear_canvas()
        self.update_select_button()
        self.populate_canvas(os.scandir(self.curFolder.path))

    def on_canvas_resize(self, event):
        """when user resizes the window"""
        if self.canvas.winfo_width() != self.canvasWidth:
            self.canvasWidth = self.canvas.winfo_width()
        if not self.loaded:
            self.clear_canvas()
            self.canvas.create_line(0, 0, self.canvasWidth, self.tree.winfo_height())

    def on_canvas_click(self, event):
        """when user clicks in canvas"""
        # get keyboard focus
        self.canvas.focus_set()
        # find item that was clicked
        items = self.canvas.find_withtag(CURRENT)
        if len(items) and items[0] in self.canvasItems:
            tile = self.canvasItems[items[0]]
            index = self.tilesOrder.index(tile)
            if event.state & 1: #shift
                if isinstance(tile, PxTileHole):
                    # shift-clicking a hole deletes holes from there to end
                    self.reflow(index, True)
                else:
                    # extend selection from last tile clicked (not inclusive) to clicked tile (inclusive)
                    try:
                        lastClickIndex = self.tilesOrder.index(self.lastTileClicked)
                    except ValueError:
                        lastClickIndex = 0
                    if index < lastClickIndex:
                        for i in range(index, lastClickIndex):
                            self.select_tile(self.tilesOrder[i], self.curSelectColor)
                    else:
                        for i in range(lastClickIndex+1, index+1):
                            self.select_tile(self.tilesOrder[i], self.curSelectColor)
            elif event.state & 4: #control
                # toggle selection of clicked tile
                if not tile.selected:
                    self.select_tile(tile, self.curSelectColor)
                else:
                    # absorb color of clicked tile before unselecting it
                    self.curSelectColor = tile.selected
                    self.select_tile(tile, False)
            elif event.state & 0x20000: #alt
                # possibly bump color (first alt-click sets current color, next one bumps color)
                if tile.selected == self.curSelectColor:
                    self.curSelectColor += 1
                    if self.curSelectColor not in selectColors:
                        self.curSelectColor = 1
                self.select_tile(tile, self.curSelectColor)
            else:
                # plain click
                if isinstance(tile, PxTileHole):
                    # clicking a hole deletes that hole and following adjacent holes
                    self.reflow(index, 'leading')
                elif not tile.selected:
                    self.select_tile(tile, self.curSelectColor)
                else:
                    # already selected, absorb color
                    self.curSelectColor = tile.selected

            # remember last tile clicked (for shift-click extension)
            self.lastTileClicked = tile
            self.update_select_button()
            if self.any_selected(self.curSelectColor):
                self.update_select_status()
            else:
                self.set_status_default()
        else:
            if self.loaded and not len(items):
                # clicked outside or between items, insert hole before next item
                # if clicked after last item, add hole at end of canvas
                ex = self.canvas.canvasx(event.x)
                ey = self.canvas.canvasy(event.y)
                holeAdded = False
                insertAtEnd = True
                for index, tile in enumerate(self.tilesOrder):
                    x, y = self.canvas.coords(tile.items[0])[:2]
                    if (ex < x and ey >= y and ey < y + tile.h):
                        self.insert_holes(index, 1)
                        holeAdded = True
                        insertAtEnd = False
                        break
                    elif ey < y:
                        insertAtEnd = False
                if insertAtEnd:
                    self.insert_holes(-1, 1)
                    holeAdded = True
                if holeAdded:
                    self.set_status("Hole added")
                else:
                    self.set_status_default()

    def select_tile(self, tile, color):
        """select a tile"""
        if not isinstance(tile, PxTileHole):
            if not color or (tile.selected and tile.selected != color):
                tile.erase_selected(self.canvas)
            if color and not tile.selected:
                tile.draw_selected(self.canvas, color)

    def any_selected(self, color=None):
        """any tiles selected?"""
        if color:
            return any(tile.selected == color for tile in self.tilesOrder)
        else:
            return any(tile.selected for tile in self.tilesOrder)

    def num_selected(self, color):
        """return number of tiles selected with specified color"""
        return len([tile for tile in self.tilesOrder if tile.selected == color])

    def select_all(self, color, filterColor=None):
        """select/unselect all"""
        for tile in self.tilesOrder:
            if not filterColor or tile.selected == filterColor:
                self.select_tile(tile, color)

    def save_selections(self):
        """return current selections"""
        selections = {}
        for tile in self.tilesOrder:
            if tile.selected:
                selections[tile.name] = tile.selected
        return selections

    def apply_selections(self, selections):
        """apply selections"""
        for name, color in selections.items():
            if name in self.tilesByName:
                self.select_tile(self.tilesByName[name], color)

    def on_canvas_dnd_motion(self, event):
        """on any mouse motion with button down"""
        if not self.dragging:
            if self.dragStart is None:
                # get canvas item under mouse
                items = self.canvas.find_withtag(CURRENT)
                if len(items) and items[0] in self.canvasItems:
                    tile = self.canvasItems[items[0]]
                    if tile.selected:
                        # drag all tiles selected with same color
                        # note you can't drag unselected tiles
                        self.dragColor = tile.selected
                        self.dragTiles = [t for t in self.tilesOrder if t.selected == self.dragColor]
                        self.dragStart = (event.x, event.y)
            elif abs(event.x - self.dragStart[0]) > 10 or abs(event.y - self.dragStart[1]) > 10:
                # have dragged far enough to call it a real drag
                self.dragging = True
                self.dragCopy = event.state & 4
                self.canvas.configure(cursor="cross_reverse" if self.dragCopy else "box_spiral")
                self.set_status("Dragging {:d} {} items".format(len(self.dragTiles),
                                                                selectColors[self.dragColor]))
    def on_canvas_dnd_release(self, event):
        """on mouse button release"""
        if self.dragging:
            w = self.top.winfo_containing(event.x_root, event.y_root)
            if w != self.canvas:
                # dnd to a different window
                items = [DndItemEnt(DirEntryFile(os.path.join(self.curFolder.path, t.name)))
                         for t in self.dragTiles]
                accepted = dnd.try_drop(w, items, self.dragCopy, event)
                nAccepted = 0
                if accepted:
                    for i, tile in enumerate(self.dragTiles):
                        if accepted is True or i < len(accepted) and accepted[i]:
                            if not self.dragCopy:
                                self.nuke_nails(tile.name)
                                self.remove_tile(tile, True)
                            nAccepted += 1
                    self.set_status("{:d} of {:d} items accepted by {}".format(nAccepted, len(items),
                                                                               dnd.get_target_name(w)))
                    self.update_select_button()
                    if nAccepted and not self.dragCopy:
                        self.sweep_out_of_order()
                else:
                    self.set_status("No items accepted")
            else:
                # dnd within same window
                targ = self.get_target_tile(event)
                if isinstance(targ, PxTileHole) and not self.dragCopy:
                    toIndex = self.tilesOrder.index(targ)
                    toIndexStart = toIndex
                    minIndex = toIndex
                    # make sure there are enough holes
                    nHoles = self.count_holes(toIndex)
                    if nHoles < len(self.dragTiles):
                        self.insert_holes(toIndex, len(self.dragTiles) - nHoles)
                    # swap dragged tiles and holes
                    for tile in self.dragTiles:
                        fromIndex = self.tilesOrder.index(tile)
                        minIndex = min(minIndex, fromIndex)
                        hole = self.tilesOrder[toIndex]
                        self.tilesOrder[fromIndex] = hole
                        self.tilesOrder[toIndex] = tile
                        toIndex += 1
                    # reflow the affected tiles
                    # must go back one because tiles we moved have invalid coordinates
                    # ok if start index goes to -1, will reflow all tiles
                    self.reflow(minIndex-1)
                    self.set_status("{:d} items moved".format(len(self.dragTiles)))
                    # deselect after drag and drop
                    self.select_all(None, self.curSelectColor)
                    self.update_select_button()
                    # check tiles just moved for OOO errors
                    self.check_out_of_order(toIndexStart, toIndex)
                    self.sweep_out_of_order()
                else:
                    self.set_status("No drop target")

        self.dragging = False
        self.dragStart = None
        self.dragTiles = None
        self.dragColor = None
        self.dragCopy = False
        self.canvas.configure(cursor="")

    def receive_drop(self, items, doCopy, event):
        """called by dnd, return true if drop accepted (or array of true/false)"""
        if not self.curFolder:
            return False
        entries = []
        result = []
        for item in items:
            accepted = False
            if isinstance(item, DndItemEnt):
                ent = item.thing
                try:
                    if doCopy:
                        newPath = self.copy_file_to_cur_folder(ent.path)
                    else:
                        newPath = self.move_file_to_cur_folder(ent.path)
                        # stash metadata in loose cache for later use
                        metacache.remove_meta_to_loose_cache(ent.path, self.env)

                    entries.append(DirEntryFile(newPath))
                    accepted = True
                except RuntimeError as e:
                    self.log_error(str(e))
            result.append(accepted)

        if len(entries):
            targ = self.get_target_tile(event)
            if isinstance(targ, PxTileHole):
                self.populate_holes(self.tilesOrder.index(targ), entries)
            else:
                # not dropped onto a hole, add to end
                self.populate_canvas(entries)
            # select the new tiles
            for ent in entries:
                if ent.name in self.tilesByName:
                    self.select_tile(self.tilesByName[ent.name], self.curSelectColor)
            self.update_select_button()
            # save meta changes
            metacache.write_all_changes(self.env)
        return result

    def get_target_tile(self, event):
        """return target tile for mouse event or None"""
        ex = event.x_root - self.canvas.winfo_rootx()
        ey = event.y_root - self.canvas.winfo_rooty()
        cx = self.canvas.canvasx(ex)
        cy = self.canvas.canvasy(ey)
        hits = self.canvas.find_overlapping(cx, cy, cx + 1, cy + 1)
        if len(hits) and hits[0] in self.canvasItems:
            return self.canvasItems[hits[0]]
        else:
            return None

    def on_canvas_key(self, event):
        """handle keyboard event for canvas"""
        if event.keycode == 46: #delete key
            tilesToDelete = [t for t in self.tilesOrder if t.selected == self.curSelectColor]
            if len(tilesToDelete):
                msg = "{:d} {} items selected, are you sure you want to delete them?".format(
                    len(tilesToDelete), selectColors[self.curSelectColor])
                if messagebox.askyesno("Confirm Delete", msg):
                    nDeleted = 0
                    for tile in tilesToDelete:
                        try:
                            self.delete_file_in_cur_folder(tile.name)
                            self.remove_tile(tile, True)
                            nDeleted += 1
                        except RuntimeError as e:
                            self.log_error(str(e))
                    self.set_status("{:d} items deleted".format(nDeleted))
                    self.sweep_out_of_order()
            else:
                self.set_status("No items selected")

    def clear_canvas(self):
        """delete all items in canvas"""
        self.canvas.delete(ALL)
        self.canvasItems = {}
        self.tiles = {}
        self.tilesOrder = []
        self.tilesByName = {}
        self.lastClickIndex = 0
        self.curSelectColor = 1
        self.nPictures = 0
        self.hTotal = tileGap / 2
        self.nails = None
        self.nailsTried = False
        self.metaDict = None
        self.metaDictRefCnt = 0


    def populate_canvas(self, entries):
        """add specified pictures to canvas
        argument is return value from scandir() or equivalent
        """
        self.canvas.configure(background="black")
        self.clear_error()
        self.set_status("Loading...")
        prevLen = len(self.tilesOrder)
        self.get_meta_dict()

        # bump start position for next tile,
        # possibly bump to next row
        def bump_position():
            nonlocal x, y, hmax
            x += self.nailSz + tileGap
            if x + self.nailSz > self.canvasWidth:
                x = tileGap / 2
                y += hmax + tileGap
                hmax = 0

        # where to start?
        if len(self.tilesOrder):
            # get cooordinates of last tile and bump
            x, y = self.canvas.coords(self.tilesOrder[-1].items[0])[:2]
            hmax = self.hTotal - y
            bump_position()
        else:
            # empty canvas
            x = tileGap / 2
            y = tileGap / 2
            hmax = 0

        # note i'm not sorting, on my system scandir returns them sorted already
        for ent in entries:
            if ent.is_file() and ent.name != "Thumbs.db":
                tile = self.make_tile(ent)
                self.add_tile(tile)
                tile.add_to_canvas(self.canvas, x, y, self.nailSz)
                self.add_canvas_item(tile)
                if tile.h > hmax:
                    hmax = tile.h
                bump_position()

        # bump to next row if partial row
        if x > tileGap:
            x = self.canvasWidth
            bump_position()
        # set scroll region to final height
        self.canvas.configure(scrollregion=(0, 0, 1, y))
        self.hTotal = y
        # scroll to top
        self.canvas.yview_moveto(0)
        self.set_status_default_or_error()
        self.loaded = True
        self.enable_buttons()
        # check tiles just added for OOO errors
        self.check_out_of_order(prevLen, len(self.tilesOrder))
        self.forget_meta_dict()

    def populate_holes(self, startIndex, entries):
        """fill hole(s) with specified files
        similarity to populate_canvas noted, but trying to factor the similar parts would be too complicated
        """
        self.clear_error()
        self.set_status("Loading...")
        prevLen = len(self.tilesOrder)
        self.get_meta_dict()

        # make sure there are enough holes
        nHoles = self.count_holes(startIndex)
        if nHoles < len(entries):
            self.insert_holes(startIndex, len(entries) - nHoles)
        index = startIndex
        for ent in entries:
            hole = self.tilesOrder[index]
            x, y = self.canvas.coords(hole.items[0])[:2]
            self.remove_tile(hole)
            tile = self.make_tile(ent)
            self.add_tile(tile, index)
            tile.add_to_canvas(self.canvas, x, y, self.nailSz)
            self.add_canvas_item(tile)
            index += 1
        self.reflow(startIndex)
        self.set_status_default_or_error()
        # check tiles just added for OOO errors
        self.check_out_of_order(prevLen, len(self.tilesOrder))
        self.forget_meta_dict()

    def reflow(self, index=-1, removeHoles=False):
        """reflow starting at specified index, optionally removing holes
        similarity to populate_canvas noted, but trying to factor the similar parts would be too complicated
        if removeHoles is 'leading', removes holes from start tile to first non-hole
        otherwise if removeHoles is truthy, remove all holes
        assumes starting tile has valid coordinates; from then on coordinates don't matter
        if index < 0 reflow entire canvas; all coordinates will be recomputed
        """
        # get coordinates of start tile
        if index >= 0 and index < len(self.tilesOrder):
            startTile = self.tilesOrder[index]
            x, y = self.canvas.coords(startTile.items[0])[:2]
            hmax = startTile.h
            # also look at earlier tiles in same row to find hmax
            for tile in reversed(self.tilesOrder[:index]):
                tiley = self.canvas.coords(tile.items[0])[1]
                if tiley < y:
                    # prior row, done looking
                    break
                elif tile.h > hmax:
                    hmax = tile.h
        else:
            # reflow entire canvas
            index = 0
            x = tileGap / 2
            y = tileGap / 2
            hmax = 0

        # bump start position for next tile,
        # possibly bump to next row
        def bump_position():
            nonlocal x, y, hmax
            x += self.nailSz + tileGap
            if x + self.nailSz > self.canvasWidth:
                x = tileGap / 2
                y += hmax + tileGap
                hmax = 0

        # note slice makes a copy which is good because the loop might mutate tilesOrder by deleting holes
        for tile in self.tilesOrder[index:]:
            if removeHoles and isinstance(tile, PxTileHole):
                self.remove_tile(tile)
            else:
                if removeHoles == 'leading':
                  removeHoles = False
                oldx, oldy = self.canvas.coords(tile.items[0])[:2]
                tile.move(self.canvas, x - oldx, y - oldy)
                if tile.h > hmax:
                    hmax = tile.h
                bump_position()

        # bump to next row if partial row
        if x > tileGap:
            x = self.canvasWidth
            bump_position()
        # set scroll region to final height
        self.canvas.configure(scrollregion=(0, 0, 1, y))
        self.hTotal = y

    def make_tile(self, ent):
        """make tile based on file extension"""
        if os.path.splitext(ent.name)[1].lower() in pic.pictureExts:
            return self.make_pic_tile(ent)
        else:
            return self.make_file_tile(ent)

    def make_pic_tile(self, ent):
        """make tile for a picture"""
        photo = None
        # try to get thumbnails if we haven't already tried
        if self.nails is None and not self.nailsTried:
            self.nailsTried = True
            try:
                folderPath = os.path.split(ent.path)[0]
                self.nails = nailcache.get_nails(folderPath, self.nailSz, self.env)
            except FileNotFoundError:
                self.log_error("No thumbnail file size {:d} in {}".format(self.nailSz, self.curFolder.path))
            except RuntimeError as e:
                self.log_error(str(e))
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
            except KeyError as e:
                # see if we can get image from loose file cache
                # note it might be PIL image or PNG data bytes, we must handle either case
                imgOrData = nailcache.get_loose_file(ent.path, self.nailSz)
                if imgOrData:
                    photo = self.make_tk_photo_image(imgOrData, ent.name)
                if photo is None:
                    self.log_error(str(e)) #no thumbnail for this file
        else:
            # no log when this fails because we've already said the xpng file is missing
            imgOrData = nailcache.get_loose_file(ent.path, self.nailSz)
            if imgOrData:
                photo = self.make_tk_photo_image(imgOrData, ent.name)

        # if still no image, try to create thumbnail on the fly
        if photo is None:
            try:
                self.log_info("Making thumbnail size {:d} for {}".format(self.nailSz, ent.name), True)
                f = open(ent.path, "rb")
                im = Image.open(f)
                im.load()
                f.close()
                im = pic.fix_image_orientation(im)
                im.thumbnail((self.nailSz, self.nailSz))
                photo = ImageTk.PhotoImage(im)
                # add PIL image to loose file cache
                nailcache.add_loose_file(ent.path, self.nailSz, im)
            except:
                self.log_error("Can't create thumbnail size {:d} for {}".format(self.nailSz, ent.name))
        # if still no image, give up and display as a file
        if photo is None:
            return self.make_file_tile(ent)
        else:
            return PxTilePic(ent.name, photo, self.get_meta_dict(0), self.env)

    def make_tk_photo_image(self, imgOrData, name):
        """make Tkinter photo image from PIL image or PNG data bytes"""
        try:
            if pic.is_pil_image(imgOrData):
                # make from PIL image
                return ImageTk.PhotoImage(imgOrData)
            else:
                # make from PNG data bytes
                return PhotoImage(format="png", data=imgOrData)
        except:
            self.log_error("Can't create Tk photo image for {}".format(name))
            return None

    def make_file_tile(self, ent):
        """make tile for a file"""
        return PxTileFile(ent.name, self.env)

    def add_tile(self, tile, index=-1):
        """add a tile
        since tile may not be on canvas, does not redraw text in case of error
        """
        if index < 0:
            index = len(self.tilesOrder)
        self.tilesOrder.insert(index, tile)
        self.tilesByName[tile.name] = tile
        if tile.id:
            self.add_tile_id(tile)
        if isinstance(tile, PxTilePic):
            self.nPictures += 1
            # update number of digits, lock in 4 once that number is seen
            if tile.id and self.numDigits != 4:
                nd = pic.get_num_digits(tile.parts)
                self.numDigits = 4 if nd >= 4 else max(nd, self.numDigits)

    def add_tile_id(self, tile):
        """add tile ID to collection, check for DUP and OOP errors
        since tile may not be on canvas, does not redraw text in case of error
        """
        if tile.id:
            if tile.id in self.tiles:
                # duplicate groovy ID
                tile.set_error(pic.DUP)
                self.log_error("Duplicate ID: {}".format(tile.name))
                otherTile = self.tiles[tile.id]
                if not otherTile.is_error(pic.DUP):
                    otherTile.set_error(pic.DUP)
                    # ok to assume other tile is on canvas
                    otherTile.redraw_text(self.canvas, self.nailSz)
                    self.log_error("Duplicate ID: {}".format(otherTile.name))
            else:
                # groovy ID is good, add to collection
                self.tiles[tile.id] = tile
                # verify ID correctly predicts the folder where item can be found
                folderId = pic.get_folder_id(tile.parts)
                if folderId not in self.folders or self.curFolder is not self.folders[folderId]:
                    tile.set_error(pic.OOP)
                    self.log_error("Picture out of place: {}".format(tile.name))

    def add_canvas_item(self, tile):
        """add tile to canvas items for click and drop target"""
        self.canvasItems[tile.items[0]] = tile

    def remove_tile(self, tile, makeHole=False):
        """remove a tile, erase from canvas and optionally replace with hole"""
        if tile.name in self.tilesByName:
            del self.tilesByName[tile.name]
        if tile.id:
            self.remove_tile_id(tile)
        if tile is self.lastTileClicked:
            self.lastTileClicked = None
        if isinstance(tile, PxTilePic):
            self.nPictures -= 1
        if len(tile.items):
            if tile.items[0] in self.canvasItems:
                del self.canvasItems[tile.items[0]]
            # save bounding box for hole
            bbox = self.canvas.bbox(tile.items[0])
            tile.erase(self.canvas)
            hole = PxTileHole(self.env) if makeHole else None
        else:
            hole = None
        try:
            i = self.tilesOrder.index(tile)
            if hole:
                # put hole in same place in order array
                self.tilesOrder[i] = hole
                hole.add_to_canvas(self.canvas, bbox)
                self.add_canvas_item(hole)
            else:
                # no hole so delete from order array
                del self.tilesOrder[i]
        except ValueError:
            self.log_error("Error removing {}, not in tilesOrder".format(tile.name))

    def remove_tile_id(self, tile):
        """remove tile ID from collection, recheck DUP errors"""
        if tile.id:
            # remove from collection
            if tile.id in self.tiles and self.tiles[tile.id] is tile:
                del self.tiles[tile.id]
            # find all other tiles with same ID
            otherTiles = [t for t in self.tilesOrder if t is not tile and t.id == tile.id]
            if len(otherTiles):
                otherTile = otherTiles[0]
                # if exactly one found, clear DUP error
                if len(otherTiles) == 1:
                    otherTile.clear_error(pic.DUP)
                    # ok to assume other tile is on canvas
                    otherTile.redraw_text(self.canvas, self.nailSz)
                # if collection is vacant for this ID, add one of them
                if tile.id not in self.tiles:
                    self.tiles[tile.id] = otherTile

    def rename_tile(self, tile, newName):
        """rename a tile"""
        if tile.name in self.tilesByName:
            del self.tilesByName[tile.name]
        self.tilesByName[newName] = tile
        if tile.id:
            self.remove_tile_id(tile)
        tile.errors = 0
        tile.set_name(newName, self.env)
        if tile.id:
            self.add_tile_id(tile)
        tile.redraw_text(self.canvas, self.nailSz)

    def count_holes(self, index):
        """count holes"""
        nHoles = 0
        for tile in self.tilesOrder[index:]:
            if isinstance(tile, PxTileHole):
                nHoles += 1
            else:
                break
        return nHoles

    def insert_holes(self, index=-1, n=1):
        """insert hole(s) at index"""
        if index >= 0:
            # insert holes(s) before specified tile
            x, y = self.canvas.coords(self.tilesOrder[index].items[0])[:2]
            for i in range(0, n):
                hole = PxTileHole(self.env)
                self.add_tile(hole, index)
                hole.add_to_canvas(self.canvas, (x, y))
                self.add_canvas_item(hole)
            self.reflow(index)
        else:
            # add hole(s) at end of canvas
            for i in range(0, n):
                hole = PxTileHole(self.env)
                self.add_tile(hole)
                # coordinates don't matter because we're about to reflow
                hole.add_to_canvas(self.canvas, (0, 0))
                self.add_canvas_item(hole)
            # reflow starting at predecessor of added holes
            # ok if start index goes to -1, will reflow all tiles
            self.reflow(len(self.tilesOrder) - n - 1)

    def do_num(self):
        """number selected tiles that aren't already numbered"""
        if self.curFolder.noncanon:
            self.log_error("Sorry, current folder is noncanonical")
        else:
            self.clear_error()
            nSelected = 0
            nChanged = 0
            lastNumSeen = 0
            tilesInGroup = []
            # find subranges of tiles to be numbered
            for tile in self.tilesOrder:
                if tile.selected == self.curSelectColor:
                    nSelected += 1
                    if isinstance(tile, PxTilePic):
                        if not tile.id:
                            # found unnumbered picture tile, add to current group
                            tilesInGroup.append(tile)
                        elif self.reformatEnab:
                            # tile is already numbered, check format
                            if self.reformat_name(tile):
                                nChanged += 1
                if tile.id and not tile.errors:
                    # found numbered tile, end current group
                    if len(tilesInGroup):
                        # stick right if next numbered tile is selected, else stick left
                        nChanged += self.number_group_of_tiles(tilesInGroup,
                                                               lastNumSeen, tile.parts.num, tile.selected)
                        tilesInGroup = []
                    # keep track of last number seen
                    lastNumSeen = tile.parts.num
            # do the last group, if any
            if len(tilesInGroup):
                nChanged += self.number_group_of_tiles(tilesInGroup, lastNumSeen, pic.MAXNUM, False)
            metacache.write_all_changes(self.env)
            if not self.lastError:
                if nSelected:
                    self.set_status("{:d} files changed".format(nChanged))
                else:
                    self.set_status("No files selected")

    def number_group_of_tiles(self, tilesInGroup, lastNumSeen, nextNumSeen, stickRight):
        """number a group of unnumbered tiles consecutively
        lastNumSeen is last numbered tile before group (or zero)
        nextNumSeen is next numbered tile after group (or MAXNUM)
        stickRight says what to do if there are more numbers available than we need
        if true, number the group based on nextNumSeen (so numbering break is before group)
        otherwise number the group based on lastNumSeen (so numbering break is after group)
        return number of tiles changed
        """
        folderId = pic.get_folder_id(self.curFolder.parts)
        nChanged = 0
        nAvail = nextNumSeen - lastNumSeen - 1
        nCanDo = 0

        # make a quick pass to see how many we can do, taking into account versions sharing same number
        prevParts = "", "", "", ""
        for tile in tilesInGroup:
            junk, ver, comment, ext = parts = pic.parse_noncanon(tile.name, self.commentMode)
            # if same name as previous but different version, use same number
            if junk == prevParts[0] and ver != prevParts[1]:
                nCanDo += 1
            elif nAvail:
                nCanDo += 1
                nAvail -= 1
            prevParts = parts

        nCantDo = len(tilesInGroup) - nCanDo

        # number by tens if possible, otherwise by ones
        lastNumSeen10 = int(lastNumSeen / 10) * 10
        if lastNumSeen10 + (nCanDo * 10) < nextNumSeen and self.want_num_by_tens():
            step = 10
            firstAvailNum = lastNumSeen10 + step
            endAvailNum = int(nextNumSeen / 10) * 10
        else:
            step = 1
            firstAvailNum = lastNumSeen + step
            endAvailNum = nextNumSeen

        # pick first number according to stickiness
        if stickRight:
            firstNum = endAvailNum - (nCanDo * 10)
            tilesToDo = tilesInGroup[nCantDo:]
            errMsgNum = nextNumSeen
            errMsgSide = "before"
        else:
            firstNum = firstAvailNum
            tilesToDo = tilesInGroup[:nCanDo]
            errMsgNum = lastNumSeen
            errMsgSide = "after"

        num = firstNum
        prevParts = "", "", "", ""
        for tile in tilesToDo:
            junk, ver, comment, ext = parts = pic.parse_noncanon(tile.name, self.commentMode)
            # if same name as previous but different version, use same number
            if junk == prevParts[0] and ver != prevParts[1]:
                num -= step
            prevParts = parts

            lumps = [folderId]
            if self.numDigits == 3 or (self.numDigits < 3 and step == 1):
                lumps.append("{:03d}{}".format(num, ver))
            else:
                lumps.append("{:04d}{}".format(num, ver))
            if comment:
                lumps.append(comment)
            newName = "-".join(lumps) + ext
            try:
                self.rename_file_in_cur_folder(tile.name, newName)
                self.rename_tile(tile, newName)
                # apply metadata from loose cache, if any
                # use newName because above rename changed name in loose cache
                self.get_meta_dict(0).restore_meta_from_loose_cache(tile.id, newName)
                nChanged += 1
                errMsgNum = num
                num += step
            except RuntimeError as e:
                self.log_error(str(e))

        if nCantDo:
            self.log_error("{:d} files {} {:d} could not be numbered".format(nCantDo, errMsgSide, errMsgNum))
        return nChanged

    def want_num_by_tens(self):
        """return true if numbering by tens is desired"""
        return self.numByTens and len(self.tilesOrder) < 500

    def reformat_name(self, tile):
        """if name is not correctly formatted, fix it and return true"""
        if (tile.id):
            if self.numDigits == 3 or (self.numDigits < 3 and not self.want_num_by_tens()):
                num = "{:03d}".format(tile.parts.num)
            else:
                num = "{:04d}".format(tile.parts.num)

            newName = "{}{}-{}{}{}".format(tile.parts.parent, tile.parts.child,
                                           tile.parts.type, num, tile.parts.ver)
            if tile.parts.comment:
                newName = "{}-{}{}".format(newName, tile.parts.comment, tile.parts.ext)
            else:
                newName = "{}{}".format(newName, tile.parts.ext)

            if newName != tile.name:
                try:
                    self.rename_file_in_cur_folder(tile.name, newName)
                    self.rename_tile(tile, newName)
                    return True
                except RuntimeError as e:
                    self.log_error(str(e))
        return False

    def do_unnum(self):
        """unnumber selected tiles"""
        self.clear_error()
        nSelected = 0
        nChanged = 0
        for tile in self.tilesOrder:
            if tile.selected == self.curSelectColor:
                nSelected += 1
                if tile.id:
                    newName = "_{}".format(tile.name)
                    try:
                        oldId = tile.id
                        newPath = self.rename_file_in_cur_folder(tile.name, newName)
                        self.rename_tile(tile, newName)
                        # save any metadata in loose cache for later use
                        self.get_meta_dict(0).remove_meta(oldId, newPath)
                        nChanged += 1
                    except RuntimeError as e:
                        self.log_error(str(e))
        self.sweep_out_of_order()
        metacache.write_all_changes(self.env)
        if not self.lastError:
            if nSelected:
                self.set_status("{:d} files changed".format(nChanged))
            else:
                self.set_status("No files selected")

    def do_sort(self):
        """sort tiles by number"""
        self.clear_error()
        # pull out the numbered tiles into a separate array
        a = [t for t in self.tilesOrder if t.is_numbered()]
        # sort them by number
        a.sort(key=lambda t: t.parts.sortNum)
        # weave in the sorted tiles with the unnumbered ones in their original order
        it = iter(a)
        self.tilesOrder = [next(it) if t.is_numbered() else t for t in self.tilesOrder]
        # repaint canvas with the new order
        self.reflow()
        # clear OOO error flags
        self.sweep_out_of_order()
        self.set_status_default()

    def set_tile_out_of_order(self, tile):
        """set out-of-order error for specified tile and redraw text"""
        if not tile.is_error(pic.OOO):
            tile.set_error(pic.OOO)
            tile.redraw_text(self.canvas, self.nailSz)
            self.log_error("Out of order: {}".format(tile.name))

    def clear_tile_out_of_order(self, tile):
        """clear out-of-order bit for specified tile and redraw text"""
        if tile.is_error(pic.OOO):
            tile.clear_error(pic.OOO)
            tile.redraw_text(self.canvas, self.nailSz)

    def check_out_of_order(self, startIndex, endIndex):
        """check range of tiles for OOO error"""
        startSortNum = 0
        endSortNum = pic.MAXSORTNUM
        # anchor the range to existing numbered tiles by expanding it by one at each end
        while startIndex > 0:
            startIndex -= 1
            if self.tilesOrder[startIndex].is_numbered():
                break
        while endIndex < len(self.tilesOrder):
            endIndex += 1
            if self.tilesOrder[endIndex-1].is_numbered():
                break
        # find first numbered tile at start of range
        # it is deemed correct by definition
        while startIndex < endIndex:
            startTile = self.tilesOrder[startIndex]
            startIndex += 1
            if startTile.is_numbered():
                self.clear_tile_out_of_order(startTile)
                startSortNum = startTile.parts.sortNum
                break
        # find last numbered tile at end of range that's greater than startSortNum
        # it is deemed correct also (other numbered tiles we pass on the way are OOO)
        while startIndex < endIndex:
            endTile = self.tilesOrder[endIndex-1]
            endIndex -= 1
            if endTile.is_numbered():
                if endTile.parts.sortNum > startSortNum:
                    self.clear_tile_out_of_order(endTile)
                    endSortNum = endTile.parts.sortNum
                    break
                else:
                    self.set_tile_out_of_order(endTile)
        # now test the remaining tiles
        # they must ascend from startSortNum but cannot exceed endSortNum
        priorSortNum = startSortNum
        for tile in self.tilesOrder[startIndex:endIndex]:
            if tile.is_numbered():
                if tile.parts.sortNum > priorSortNum and tile.parts.sortNum < endSortNum:
                    self.clear_tile_out_of_order(tile)
                    priorSortNum = tile.parts.sortNum
                else:
                    self.set_tile_out_of_order(tile)

    def sweep_out_of_order(self):
        """sweep all tiles and clear OOO errors that are no longer true
        do this when tiles have been moved or removed, possibly fixing OOO errors
        rely on above function to set OOO errors in the local context of moved or added tiles
        this function also clears any stray OOO errors on unnumbered tiles
        """
        def check_these(tiles, priorSortNum, endSortNum):
            for tile in tiles:
                if tile.parts.sortNum > priorSortNum and tile.parts.sortNum < endSortNum:
                    self.clear_tile_out_of_order(tile)
                    priorSortNum = tile.parts.sortNum

        # find ranges of numbered tiles with OOO errors
        # check each range using adjacent numbered tiles to define the correct numbering for that range
        startSortNum = 0
        tilesToCheck = []
        for tile in self.tilesOrder:
            if tile.is_numbered():
                if tile.is_error(pic.OOO):
                    tilesToCheck.append(tile)
                else:
                    if len(tilesToCheck):
                        check_these(tilesToCheck, startSortNum, tile.parts.sortNum)
                        tilesToCheck = []
                    startSortNum = tile.parts.sortNum
            else:
                self.clear_tile_out_of_order(tile)
        if len(tilesToCheck):
            check_these(tilesToCheck, startSortNum, pic.MAXSORTNUM)

    def rename_file_in_cur_folder(self, oldName, newName):
        """rename file in current folder, return new path"""
        oldPath = os.path.join(self.curFolder.path, oldName)
        newPath = os.path.join(self.curFolder.path, newName)
        self.log_info("Renaming {} to {}".format(oldPath, newName))
        if os.path.exists(newPath):
            raise RuntimeError("Rename failed for {}: File already exists".format(oldPath))
        try:
            shutil.move(oldPath, newPath)
            self.nuke_nails(oldName)
            nailcache.change_loose_file(oldPath, newPath)
            metacache.change_loose_meta(oldPath, newPath)
            return newPath
        except BaseException as e:
            raise RuntimeError("Rename failed for {}: {}".format(oldPath, str(e)))

    def delete_file_in_cur_folder(self, name):
        """delete file in current folder"""
        path = os.path.join(self.curFolder.path, name)
        self.log_info("Deleting {}".format(path))
        try:
            os.remove(path)
            self.nuke_nails(name)
            nailcache.clear_loose_file(path)
            metacache.clear_loose_meta(path)
        except BaseException as e:
            raise RuntimeError("Delete failed for {}: {}".format(path, str(e)))

    def move_file_to_cur_folder(self, oldPath):
        """move file to current folder, return new path"""
        newPath = os.path.join(self.curFolder.path, os.path.basename(oldPath))
        self.log_info("Moving {} to {}".format(oldPath, self.curFolder.path))
        if os.path.exists(newPath):
            raise RuntimeError("Move failed for {}: File already exists".format(oldPath))
        try:
            shutil.move(oldPath, newPath)
            nailcache.change_loose_file(oldPath, newPath)
            metacache.change_loose_meta(oldPath, newPath)
            return newPath
        except BaseException as e:
            raise RuntimeError("Move failed for {}: {}".format(oldPath, str(e)))

    def copy_file_to_cur_folder(self, oldPath):
        """copy file to current folder, return new path"""
        newPath = os.path.join(self.curFolder.path, os.path.basename(oldPath))
        self.log_info("Copying {} to {}".format(oldPath, self.curFolder.path))
        if os.path.exists(newPath):
            raise RuntimeError("Copy failed for {}: File already exists".format(oldPath))
        try:
            shutil.copy(oldPath, newPath)
            nailcache.change_loose_file(oldPath, newPath)
            metacache.change_loose_meta(oldPath, newPath)
            return newPath
        except BaseException as e:
            raise RuntimeError("Copy failed for {}: {}".format(oldPath, str(e)))

    def nuke_nails(self, name=None):
        """blow away the nails file for this folder
        put the images in the loose file cache so we can keep using them,
        and the nailer can use them to build a new nails file
        if name specified, nuke only if that name appears in nails file
        """
        # preload all sizes
        any = False
        for sz in pic.nailSizes:
            try:
                tmpNails = nailcache.get_nails(self.curFolder.path, sz, self.env)
                any = name is None or tmpNails.has_name(name)
            except:
                pass
        if any:
            # explode any nails files we have in cache for this folder to the loose file cache
            nailcache.explode_nails(self.curFolder.path)
            self.log_info("{} loose files after exploding".format(nailcache.looseCount))
            # clear them from the cache
            nailcache.clear_nails(self.curFolder.path, self.env)
            self.nails = None
            self.nailsTried = True
            # delete the actual files
            for sz in pic.nailSizes:
                nails.delete_nails(self.curFolder.path, sz, self.env)
                # turn file tile into a hole
                name = nails.build_file_name(sz)
                if name in self.tilesByName:
                    self.remove_tile(self.tilesByName[name], True)

    def on_canvas_rclick(self, event):
        """when user right-clicks in canvas"""
        # find item that was clicked
        items = self.canvas.find_withtag(CURRENT)
        if len(items) and items[0] in self.canvasItems:
            self.popMenuTile = self.canvasItems[items[0]]
            self.popMenu.post(event.x_root, event.y_root)

    def on_canvas_doubleclick(self, event):
        """when user double clicks in canvas"""
        # find item that was clicked
        items = self.canvas.find_withtag(CURRENT)
        if len(items) and items[0] in self.canvasItems:
            tile = self.canvasItems[items[0]]
            print("TODO: double click for {}".format(tile.name))

    def do_delete(self):
        """menu delete"""
        msg = "Are you sure you want to delete {}?".format(self.popMenuTile.name)
        if messagebox.askyesno("Confirm Delete", msg):
            try:
                self.delete_file_in_cur_folder(self.popMenuTile.name)
                self.remove_tile(self.popMenuTile, True)
                self.set_status("1 item deleted")
                self.sweep_out_of_order()
            except RuntimeError as e:
                self.log_error(str(e))

    def do_rename(self):
        """menu rename"""
        PxRenameDialog(self, self.popMenuTile)

    def do_rename_apply(self, tile, newName):
        """when ok clicked in rename menu"""
        try:
            self.rename_file_in_cur_folder(tile.name, newName)
            self.rename_tile(tile, newName)
            self.set_status("1 item renamed")
            self.sweep_out_of_order()
        except RuntimeError as e:
            self.log_error(str(e))

    def do_edit_meta(self):
        """menu edit metadata"""
        PxMetaDialog(self, self.popMenuTile)

    def do_close_menu(self):
        """menu close"""
        self.popMenu.unpost()

    def goto(self, ids):
        """possibly change folder then scroll to specified tile"""
        ids = tkit.make_array(ids)
        id0 = ids[0]
        parts = pic.parse_file(id0, self.env)
        if (parts):
            folderId = pic.get_folder_id(parts)
            if folderId in self.folders:
                folder = self.folders[folderId]
                if (folder is not self.curFolder):
                    self.log_info("Switching folder for goto {}".format(id0))
                    self.load_folder(folder)
                if id0 in self.tiles:
                    # select first tile
                    tile0 = self.tiles[id0]
                    self.select_all(None, self.curSelectColor)
                    self.select_tile(tile0, self.curSelectColor)
                    self.scroll_into_view(tile0)
                    self.set_status_default()
                    # select additional tiles
                    for id in ids[1:]:
                        if id in self.tiles:
                            tile = self.tiles[id]
                            self.select_tile(tile, self.curSelectColor)
                else:
                    self.log_error("Goto failed, {} not found".format(id0))
            else:
                self.log_error("Goto failed, folder {} not found".format(folderId))
        else:
            self.log_error("Goto failed, can't parse {}".format(id))

    def scroll_into_view(self, tile):
        """scroll tile into view"""
        if not self.is_tile_in_view(tile):
            x, y = self.canvas.coords(tile.items[0])[:2]
            self.canvas.yview_moveto(float(max(0, y - tileGap)) / self.hTotal)

    def is_tile_in_view(self, tile):
        """is tile in view?"""
        x, y = self.canvas.coords(tile.items[0])[:2]
        top = float(max(0, y - tileGap)) / self.hTotal
        bottom = float(y + tile.h) / self.hTotal
        slider = self.canvasScroll.get()
        return top >= slider[0] and bottom <= slider[1]

    def get_meta_dict(self, bump=1):
        """get meta dictionary for current folder
        usually bump ref count to hold dictionary for later use
        call forget_meta_dict() when you are done with it
        this helps ensure we are not stuck with an old copy of the dictionary
        for example suppose we get dict from metacache and hold it for a long time
        meanwhile metacache decides to clear that dict from cache
        then somebody loads it again and makes changes
        we would not see the changes because we're pointing to a different dict object
        if you just need the dictionary once, pass bump=0 to skip the ref count business
        """
        if self.metaDict:
            self.metaDictRefCnt += bump
        else:
            self.metaDict = metacache.get_meta_dict(self.curFolder.path, self.env)
            self.metaDictRefCnt = bump
        return self.metaDict

    def forget_meta_dict(self):
        """done with meta dictionary"""
        self.metaDictRefCnt -= 1
        if self.metaDictRefCnt == 0:
            self.metaDict = None

    def update_from_meta(self, ids):
        """update specified IDs from metadata"""
        # prefetch meta dict
        self.get_meta_dict()
        for id in tkit.make_array(ids):
            if id in self.tiles:
                self.update_tile_from_meta(self.tiles[id])
        self.forget_meta_dict()

    def update_tile_from_meta(self, tile):
        """update tile from metadata"""
        if tile.id:
            self.get_meta_dict()
            tile.set_rating(self.metaDict.get_rating(tile.id))
            tile.set_caption(self.metaDict.get_caption(tile.id))
            tile.redraw_text(self.canvas, self.nailSz)
            tile.redraw_icon(self.canvas)
            self.forget_meta_dict()
