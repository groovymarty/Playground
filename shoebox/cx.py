# shoebox.cx

import os, shutil
from tkinter import *
from tkinter import ttk, messagebox, simpledialog
from PIL import Image
import ImageTk
from shoebox import pic, nails, nailcache, dnd, metacache, contents, finder, px
from shoebox.dnd import DndItemEnt, DndItemId
from shoebox.cxfolder import CxFolder
from shoebox.pxtile import PxTilePic, PxTileFile, PxTileFolder, PxTileHole, selectColors
from shoebox.viewer import Viewer
from shoebox.contents import Contents
from shoebox.metadict import MetaDictLayer, get_meta_default
from tkit.direntry import DirEntryFile, DirEntryDir
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

class CxMetaDialog(simpledialog.Dialog):
    def __init__(self, cx, tile):
        self.cx = cx
        self.tile = tile
        simpledialog.Dialog.__init__(self, cx.top, title="Edit Metadata - {}".format(cx.myName))

    def body(self, master):
        master.columnconfigure(1, weight=1, minsize=500)
        Label(master, text="Picture ID:").grid(row=0, sticky=W)
        Label(master, text=self.tile.id).grid(row=0, column=1, sticky=W)
        Label(master, text="Caption").grid(row=1, sticky=W)
        self.caption = ttk.Entry(master)
        self.caption.grid(row=1, column=1, sticky=(W,E))
        self.caption.insert(0, self.cx.get_meta_value(self.tile.id, 'caption'))

    def apply(self):
        caption = self.caption.get()
        if caption:
            self.cx.set_meta_value(self.tile.id, 'caption', caption)
        else:
            self.cx.unset_meta_value(self.tile.id, 'caption')
        self.cx.update_tile_from_meta(self.tile)
        self.cx.write_contents()

class Cx(LogHelper, WidgetHelper):
    def __init__(self):
        self.env = {}
        LogHelper.__init__(self, self.env)
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1

        # create top level window
        self.top = Toplevel()
        self.myName = "Cx {:d}".format(self.instNum)
        self.styleRoot = "Cx{:d}".format(self.instNum)
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
        self.tiles = {} #groovy id to tile object
        self.tilesOrder = [] #array of tiles in display order
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
        self.popMenu.add_command(label="Edit Metadata", command=self.do_edit_meta)
        self.popMenu.add_command(label="Add Source Folder", command=self.do_add_source_folder)
        self.popMenu.add_command(label="Delete", command=self.do_delete)
        self.popMenu.add_separator()
        self.popMenu.add_command(label="[X] Close Menu", command=self.do_close_menu)
        self.popMenuTile = None

        self.lastError = ""
        self.curFolder = None
        self.cont = None
        self.loaded = False
        self.nPictures = 0
        self.viewer = None
        self.folders = {}  # folder id to folder
        self.rootFolder = self.scan_for_contents(DirEntryDir("."), True)
        self.rootFolder.iid = ""
        self.folders[""] = self.rootFolder
        self.populate_tree(self.rootFolder)
        self.set_status_default_or_error()
        self.pxInstNum = None
        instances.append(self)

    def on_destroy(self, ev):
        """called when my top-level window is closed
        this is the easiest and most common way to destroy Cx,
        and includes the case where the entire shoebox application is shut down
        """
        self.top = None
        self.destroy()

    def destroy(self):
        """destroy and clean up this Cx
        in Python you don't really destroy objects, you just remove all references to them
        so this function removes all known references then closes the top level window
        note this will result in a second call from the on_destroy event handler; that's ok
        """
        dnd.remove_target(self.canvas)
        self.close_log_windows()
        if self.viewer:
            self.viewer.destroy()
            self.viewer = None
        if self in instances:
            instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    def __del__(self):
        """Cx destructor"""
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
        if self.curFolder:
            selections = self.save_selections()
            self.load_folder(self.curFolder)
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

    def update_select_status(self):
        """update status to say what's selected"""
        self.set_status("{:d} items selected {}".format(self.num_selected(self.curSelectColor),
                                                        selectColors[self.curSelectColor]))

    def do_log(self):
        """when Log button clicked"""
        self.open_log_window("Log - {}".format(self.myName))

    def enable_buttons(self, enable=True):
        """enable/disable buttons"""
        self.enable_widget(self.refreshButton, enable)
        self.enable_widget(self.sizeButton, enable)
        self.enable_widget(self.selectButton, enable)

    def scan_for_contents(self, dirEnt, isRoot=False):
        """scan directory tree for contents
        if directory has contents.json, or any child directory does, return folder object
        otherwise return None
        """
        # make sure directory name is canonical before scanning
        parts = pic.parse_folder(dirEnt.name, self.env)
        if parts or isRoot:
            children = []
            contFound = False
            for ent in os.scandir(dirEnt.path):
                if ent.is_dir():
                    child = self.scan_for_contents(ent)
                    if child:
                        children.append(child)
                else:
                    if ent.name == contents.contentsFileName:
                        contFound = True
            # contents found in this directory or any child?
            if contFound or len(children):
                id = "" if isRoot else parts.id
                return CxFolder(children, id, dirEnt.name, dirEnt.path)

        # no contents or noncanonical, forget this one
        return None

    def populate_tree(self, parent):
        """populate tree with children of specified folder"""
        for child in parent.children:
            iid = self.tree.insert(parent.iid, 'end', text=child.name)
            self.treeItems[iid] = child
            child.iid = iid
            self.folders[child.id] = child
            self.populate_tree(child)

    def on_tree_select(self, event):
        """when user clicks tree item"""
        sel = self.tree.selection()
        if sel and sel[0] in self.treeItems:
            folder = self.treeItems[sel[0]]
            # load_folder() selects the tree item again, so this test is important to avoid an infinite loop
            if folder != self.curFolder:
                self.load_folder(folder)

    def load_folder(self, folder):
        """load specified folder"""
        self.clear_error()
        self.curFolder = folder
        self.top.title("{} - {}".format(self.myName, self.curFolder.path[2:]))
        # make sure the folder is selected and visible in the tree view
        self.tree.selection_set(folder.iid)
        self.tree.see(folder.iid)
        self.clear_canvas()
        self.update_select_button()
        self.cont = Contents(self.curFolder.path, self.env)
        finder.clear_cache()
        entries = []
        for id in self.cont.pictures:
            parts = pic.parse_file(id)
            if parts:
                path = finder.find_file(parts.id, parts)
                if path:
                    ent = DirEntryFile(path)
                else:
                    # ID not found, make special entry so it will have a tile on the canvas
                    self.log_error("{} not found".format(id))
                    ent = self.make_not_found_entry(id)
                entries.append(ent)
            else:
                self.log_error("Can't parse {}".format(id))
        for id in self.cont.folders:
            parts = pic.parse_folder(id)
            if parts:
                path = finder.find_folder(parts.id, parts)
                if path:
                    ent = DirEntryDir(path)
                else:
                    # ID not found, make special entry so it will have a tile on the canvas
                    self.log_error("{} not found".format(id))
                    ent = self.make_not_found_entry(id)
                entries.append(ent)
            else:
                self.log_error("Can't parse {}".format(id))
        self.populate_canvas(entries)

    def make_not_found_entry(self, id):
        """make a special dir entry representing a not found ID
        make_tile() will see this and make a file tile with NF error bit set
        """
        return DirEntryFile("{}.not_found".format(id))

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
                    self.set_select_color(tile.selected)
                    self.select_tile(tile, False)
            elif event.state & 0x20000: #alt
                # possibly bump color (first alt-click sets current color, next one bumps color)
                if tile.selected == self.curSelectColor:
                    self.set_select_color(self.curSelectColor + 1)
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
                    self.set_select_color(tile.selected)

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

    def set_select_color(self, color):
        """set select color"""
        if color not in selectColors:
            color = 1
        if color != self.curSelectColor:
            self.curSelectColor = color
            s = ttk.Style()
            s.configure(self.styleRoot+'.Select.TButton', background=selectColors[color])

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
                items = [DndItemId(t.id) for t in self.dragTiles if t.id]
                accepted = dnd.try_drop(w, items, self.dragCopy, event)
                nAccepted = 0
                if accepted:
                    for i, tile in enumerate(self.dragTiles):
                        if accepted is True or i < len(accepted) and accepted[i]:
                            if not self.dragCopy:
                                self.remove_tile(tile, True)
                            nAccepted += 1
                    self.set_status("{:d} of {:d} items accepted by {}".format(nAccepted, len(items),
                                                                               dnd.get_target_name(w)))
                    self.update_select_button()
                    self.write_contents()
                else:
                    self.set_status("No items accepted")
            else:
                # dnd within same window
                targ = self.get_target_tile(event)
                if isinstance(targ, PxTileHole) and not self.dragCopy:
                    toIndex = self.tilesOrder.index(targ)
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
                    self.write_contents()
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
            if isinstance(item, DndItemEnt) and doCopy:
                ent = item.thing
                if self.is_valid_ext(ent):
                    entries.append(ent)
                    accepted = True
            elif isinstance(item, DndItemId):
                # accept all IDs even if not found
                id = item.thing
                accepted = True
                filePath = finder.find_file(id)
                if filePath:
                    entries.append(DirEntryFile(filePath))
                else:
                    folderPath = finder.find_folder(id)
                    if folderPath:
                        entries.append(DirEntryDir(folderPath))
                    else:
                        # make special entry for not found ID
                        entries.append(self.make_not_found_entry(id))
            result.append(accepted)

        if len(entries):
            self.clear_error()
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
            self.write_contents()
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
                        self.remove_tile(tile, True)
                        nDeleted += 1
                    self.set_status("{:d} items deleted".format(nDeleted))
                    self.write_contents()
            else:
                self.set_status("No items selected")

    def write_contents(self):
        """update contents object and write to contents.meta file"""
        # collect pictures in our current order
        # be sure to include "not found" IDs which are represented as file tiles
        pictures = []
        videos = []
        folders = []
        for tile in self.tilesOrder:
            if isinstance(tile, PxTilePic):
                pictures.append(tile.id)
            elif isinstance(tile, PxTileFolder):
                folders.append(tile.id)
            elif isinstance(tile, PxTileFile) and tile.is_error(pic.NF):
                # all not-found items turn into file tiles, so we have to reverse-engineer
                # what container array they came from, based on the ID
                # this is a little clumsy but it works well enough
                parts = pic.parse_file(tile.id)
                if parts:
                    if parts.type == 'V':
                        videos.append(tile.id)
                    else:
                        pictures.append(tile.id)
                else:
                    parts = pic.parse_folder(tile.id)
                    if parts:
                        folders.append(tile.id)
                    else:
                        self.log_error("Can't parse not-found item ID: {}".format(tile.id))
        self.cont.pictures = pictures
        self.cont.videos = videos
        self.cont.folders = folders
        self.cont.write()

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
        self.metaDict = None
        self.metaDictRefCnt = 0

    def populate_canvas(self, entries):
        """add specified pictures to canvas
        argument is return value from scandir() or equivalent
        """
        self.canvas.configure(background="black")
        self.set_status("Loading...")

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
            tile = self.make_tile(ent)
            if tile is not None:
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

    def populate_holes(self, startIndex, entries):
        """fill hole(s) with specified files
        similarity to populate_canvas noted, but trying to factor the similar parts would be too complicated
        """
        self.set_status("Loading...")

        # make sure there are enough holes
        nHoles = self.count_holes(startIndex)
        if nHoles < len(entries):
            self.insert_holes(startIndex, len(entries) - nHoles)
        index = startIndex
        for ent in entries:
            hole = self.tilesOrder[index]
            x, y = self.canvas.coords(hole.items[0])[:2]
            tile = self.make_tile(ent)
            if tile is not None:
                self.remove_tile(hole)
                self.add_tile(tile, index)
                tile.add_to_canvas(self.canvas, x, y, self.nailSz)
                self.add_canvas_item(tile)
                index += 1
        self.reflow(startIndex)
        self.set_status_default_or_error()

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

    def is_valid_ext(self, ent):
        """is file extension recognized as valid?"""
        return os.path.splitext(ent.name)[1].lower() in pic.pictureExts

    def make_tile(self, ent):
        """make tile based on file extension"""
        if ent.is_file():
            ext = os.path.splitext(ent.name)[1].lower()
            if ext in pic.pictureExts:
                return self.make_pic_tile(ent)
            elif ext == ".not_found":
                # special entry representing ID not found
                # strip extension to recover ID from file name
                # make file tile and set "not found" error bit
                tile = self.make_file_tile(DirEntryFile(os.path.splitext(ent.name)[0]))
                tile.set_error(pic.NF)
                tile.id = tile.name
                return tile
            else:
                return self.make_file_tile(ent)
        else:
            return self.make_folder_tile(ent)

    def make_pic_tile(self, ent):
        """make tile for a picture"""
        photo = None
        nails = None
        folderPath = os.path.split(ent.path)[0]
        # try to get thumbnails
        try:
            nails = nailcache.get_nails(folderPath, self.nailSz, self.env)
        except FileNotFoundError:
            self.log_error("No thumbnail file size {:d} in {}".format(self.nailSz, folderPath))
        except RuntimeError as e:
            self.log_error(str(e))
        # try to get image from thumbnails
        if nails is not None:
            try:
                data = nails.get_by_name(ent.name)
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
            md = self.get_layered_meta_dict(folderPath)
            tile = PxTilePic(ent.name, photo, md, self.env)
            tile.ent = ent
            return tile

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

    def make_folder_tile(self, ent):
        """make tile for a folder"""
        return PxTileFolder(ent.name, self.env)

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

    def add_tile_id(self, tile):
        """add tile ID to collection, no error check
        """
        if tile.id:
            # add to collection
            self.tiles[tile.id] = tile

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
        """remove tile ID from collection"""
        if tile.id:
            # remove from collection
            if tile.id in self.tiles and self.tiles[tile.id] is tile:
                del self.tiles[tile.id]

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
            if isinstance(tile, PxTilePic):
                if event.state & 4: #control
                    # double click is goofy because you also get single click event first
                    # using control as modifier because control-click does least "damage" compared
                    # to shift (which expands selection) and alt (which changes selection color)
                    # the initial control-click event inverts selection, what to do about it?
                    # let's force the tile selected so UX is similar to plain double click (below)
                    self.select_tile(tile, self.curSelectColor)
                    self.update_select_button()
                    self.update_select_status()
                    # send Px to the clicked picture
                    pxInst = self.get_px_instance()
                    if pxInst:
                        pxInst.goto(tile.id)
                else:
                    # tell viewer to display the clicked picture
                    if self.viewer is None:
                        self.viewer = Viewer(self)
                    self.viewer.set_picture(self.tilesOrder.index(tile))
                    # viewer will select the clicked picture in left or right pane color
            elif isinstance(tile, PxTileFolder):
                pxInst = self.get_px_instance()
                if pxInst:
                    pxInst.goto_folder(tile.id)

    def get_px_instance(self):
        pxInst = px.get_instance(self.pxInstNum)
        if pxInst:
            oldInstNum = self.pxInstNum
            self.pxInstNum = pxInst.instNum
            if pxInst.instNum != oldInstNum and oldInstNum is not None:
                self.set_status("Can't find Px {:d}, switching to Px {:d}".format(oldInstNum, pxInst.instNum))
        else:
            self.set_status("No Px found, please create one")
            self.pxInstNum = None
        return pxInst

    def goto(self, folderId):
        """change to specified folder"""
        if folderId in self.folders:
            if self.folders[folderId] != self.curFolder:
                self.load_folder(self.folders[folderId])
        else:
            self.log_error("Goto failed, folder {} not found".format(folderId))

    def goto_index(self, index, selectColor=None):
        """select and scroll to specified tile"""
        if selectColor is None:
            selectColor = self.curSelectColor
        try:
            tile = self.tilesOrder[index]
            self.select_all(None, selectColor)
            self.select_tile(tile, selectColor)
            self.scroll_into_view(tile)
            self.update_select_status()
            self.update_select_button()
        except IndexError:
            self.log_error("Goto failed, index {:d} not found".format(index))

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

    def get_tile_path(self, tile):
        return tile.ent.path

    def get_tile_meta_dict(self, tile):
        folderPath = os.path.split(tile.ent.path)[0]
        return self.get_layered_meta_dict(folderPath)

    def get_layered_meta_dict(self, folderPath):
        """return layered metadata dictionary for specified folder
        contents metadata, if any, overrides values from the original picture metadata
        so for example contents meta can specify a different caption for a picture
        """
        md = metacache.get_meta_dict(folderPath, self.env)
        return MetaDictLayer(md, self.cont.meta)

    def update_tile_from_meta(self, tile):
        """update tile from metadata"""
        if tile.id:
            md = self.get_tile_meta_dict(tile)
            tile.set_rating(md.get_rating(tile.id))
            tile.set_caption(md.get_caption(tile.id))
            tile.redraw_text(self.canvas, self.nailSz)
            tile.redraw_icon(self.canvas)

    def do_delete(self):
        """menu delete"""
        msg = "Are you sure you want to delete {}?".format(self.popMenuTile.name)
        if messagebox.askyesno("Confirm Delete", msg):
            self.remove_tile(self.popMenuTile, True)
            self.set_status("1 item deleted")
            self.write_contents()

    def do_edit_meta(self):
        """menu edit metadata"""
        CxMetaDialog(self, self.popMenuTile)

    def do_add_source_folder(self):
        """menu add source folder"""
        self.clear_error()
        folderId = None
        if isinstance(self.popMenuTile, PxTilePic):
            folderId = pic.get_folder_id(self.popMenuTile.parts)
        elif isinstance(self.popMenuTile, PxTileFolder):
            folderId = pic.get_parent_id(self.popMenuTile.parts)
        if folderId:
            folderPath = finder.find_folder(folderId)
            if folderPath:
                self.populate_canvas([DirEntryDir(folderPath)])
                self.write_contents()
            else:
                self.log_error("Folder {} not found".format(folderId))
        else:
            self.log_error("No source folder for selected tile")
        self.set_status_default_or_error()

    def do_close_menu(self):
        """menu close"""
        self.popMenu.unpost()

    def get_meta_value(self, id, prop, default=None):
        """get value from contents metadata"""
        try:
            return self.cont.meta[id][prop]
        except KeyError:
            if default is None:
                return get_meta_default(prop)
            else:
                return default

    def set_meta_value(self, id, prop, val):
        """set value in contents metadata"""
        if id not in self.cont.meta:
            self.cont.meta[id] = {}
        self.cont.meta[id][prop] = val

    def unset_meta_value(self, id, prop):
        """remove value from contents metadata"""
        if id in self.cont.meta:
            if prop in self.cont.meta[id]:
                del self.cont.meta[id][prop]
            if len(self.cont.meta[id].keys()) == 0:
                del self.cont.meta[id]
