# shoebox.px

import os, shutil
from tkinter import *
from tkinter import ttk
from PIL import Image
import ImageTk
from shoebox import pic, nailcache, dnd
from shoebox.dnd import DndItemEnt
from shoebox.nailer import Nailer
from shoebox.pxfolder import PxFolder
from shoebox.pxtile import PxTilePic, PxTileFile, selectColors
from tkit.direntry import DirEntryFile
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
        self.title = "Px {:d}".format(self.instNum)
        self.styleRoot = "Px{:d}".format(self.instNum)
        self.top.title(self.title)
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
        self.canvasItems = {} #canvas id of image to tile object
        self.canvasWidth = 0
        self.hTotal = 0
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_dnd_motion)
        self.canvas.bind('<ButtonRelease>', self.on_canvas_dnd_release)
        dnd.add_target(self.canvas, self, self.title)

        self.lastError = ""
        self.curFolder = None
        self.nails = None
        self.nailsTried = False
        self.loaded = False
        self.nPictures = 0
        self.rootFolder = PxFolder(None, "", ".", "")
        self.folders = {"": self.rootFolder} #folder id to folder object
        self.populate_tree(self.rootFolder)
        self.set_status_default_or_error()
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
        dnd.remove_target(self.canvas)
        self.close_log_windows()
        if self in instances:
            instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    # Px destructor
    def __del__(self):
        self.destroy() #probably already called
        LogHelper.__del__(self)

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
        selections = self.save_selections()
        self.clear_canvas()
        self.populate_canvas(os.scandir(self.curFolder.path))
        self.apply_selections(selections)

    # when Small/Large button clicked
    def toggle_nail_size(self):
        i = pic.nailSizes.index(self.nailSz)
        i = (i + 1) % len(pic.nailSizes)
        self.nailSz = pic.nailSizes[i]
        i = (i + 1) % len(pic.nailSizes)
        self.sizeButton.configure(text=pic.nailSizeNames[i])
        self.do_refresh()

    # when Select All/None button clicked
    def toggle_select_all(self):
        if self.any_selected():
            self.select_all(False)
            self.lastTileClicked = None
        else:
            self.select_all(self.curSelectColor)
        self.update_select_button()

    # update Select All/None button
    def update_select_button(self):
        if any(tile.selected for tile in self.tilesOrder):
            self.selectButton.configure(text="Select None")
        else:
            self.selectButton.configure(text="Select All")
        s = ttk.Style()
        s.configure(self.styleRoot+'.Select.TButton', background=selectColors[self.curSelectColor])
        self.set_status("{:d} items selected {}".format(self.num_selected(self.curSelectColor),
                                                        selectColors[self.curSelectColor]))

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
        self.enable_widget(self.selectButton, enable)
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
            parentId = pic.get_parent_id(folder.parts)
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
            self.populate_canvas(os.scandir(self.curFolder.path))

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
            index = self.tilesOrder.index(tile)
            if event.state & 1: #shift
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
                if not tile.selected:
                    self.select_tile(tile, self.curSelectColor)
                else:
                    # already selected, absorb color
                    self.curSelectColor = tile.selected

            # remember last tile clicked (for shift-click extension)
            self.lastTileClicked = tile
            self.update_select_button()
        else:
            self.set_status_default()

    # select a tile
    def select_tile(self, tile, color):
        if not color or (tile.selected and tile.selected != color):
            tile.erase_selected(self.canvas)
        if color and not tile.selected:
            tile.draw_selected(self.canvas, color)

    # any tiles selected?
    def any_selected(self):
        return any(tile.selected for tile in self.tilesOrder)

    # return number of tiles selected with specified color
    def num_selected(self, color):
        return len([tile for tile in self.tilesOrder if tile.selected == color])

    # select/unselect all
    def select_all(self, color):
        for tile in self.tilesOrder:
            self.select_tile(tile, color)

    # return current selections
    def save_selections(self):
        selections = {}
        for tile in self.tilesOrder:
            if tile.selected:
                selections[tile.name] = tile.selected
        return selections

    # apply selections
    def apply_selections(self, selections):
        for name, color in selections.items():
            if name in self.tilesByName:
                self.select_tile(self.tilesByName[name], color)

    # on any mouse motion with button down
    def on_canvas_dnd_motion(self, event):
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
                self.canvas.configure(cursor="box_spiral")
                self.set_status("Dragging {:d} {} items".format(len(self.dragTiles),
                                                                selectColors[self.dragColor]))

    # on mouse button release
    def on_canvas_dnd_release(self, event):
        if self.dragging:
            w = self.top.winfo_containing(event.x_root, event.y_root)
            if w != self.canvas:
                items = [DndItemEnt(DirEntryFile(os.path.join(self.curFolder.path, t.name)))
                         for t in self.dragTiles]
                accepted = dnd.try_drop(w, items)
                nAccepted = 0
                if accepted:
                    for index, tile in enumerate(self.dragTiles):
                        if accepted is True or index < len(accepted) and accepted[index]:
                            self.remove_tile(tile)
                            nAccepted += 1
                    self.set_status("{:d} of {:d} items accepted by {}".format(nAccepted, len(items),
                                                                               dnd.get_target_name(w)))
                else:
                    self.set_status("No items accepted")
            else:
                self.set_status_default()

        self.dragging = False
        self.dragStart = None
        self.dragTiles = None
        self.dragColor = None
        self.canvas.configure(cursor="")

    # called by dnd, return true if drop accepted (or array of true/false)
    def receive_drop(self, items):
        if self.curFolder:
            entries = []
            result = []
            for item in items:
                accepted = False
                if item.kind == dnd.ENT:
                    ent = item.thing
                    try:
                        self.log_info("Moving {} to {}".format(ent.path, self.curFolder.path))
                        shutil.move(ent.path, self.curFolder.path)
                        entries.append(ent)
                        accepted = True
                    except shutil.Error as e:
                        self.log_error("Could not accept {}: {}".format(item.thing.path, str(e)))
                result.append(accepted)
            if len(entries):
                self.populate_canvas(entries)
            return result
        else:
            return False

    # delete all items in canvas
    def clear_canvas(self):
        self.canvas.delete(ALL)
        self.canvasItems = {}
        self.tiles = {}
        self.tilesOrder = []
        self.tilesByName = {}
        self.lastClickIndex = 0
        self.curSelectColor = 1
        self.nPictures = 0
        self.hTotal = tileGap / 2

    # add specified pictures to canvas
    # argument is return value from scandir() or equivalent
    def populate_canvas(self, entries):
        self.canvas.configure(background="black")
        self.clear_error()
        self.set_status("Loading...")
        self.nails = None
        self.nailsTried = False
        x = tileGap / 2
        y = self.hTotal
        hmax = 0

        # note i'm not sorting, on my system scandir returns them sorted already
        for ent in entries:
            if ent.is_file() and ent.name != "Thumbs.db":
                if os.path.splitext(ent.name)[1].lower() in pic.pictureExts:
                    self.nPictures += 1
                    tile = self.make_pic_tile(ent)
                else:
                    tile = self.make_file_tile(ent)

                self.add_tile(tile)
                tile.add_to_canvas(self.canvas, x, y, self.nailSz)
                self.canvasItems[tile.items[0]] = tile
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
        self.hTotal = y
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
                folderPath = os.path.split(ent.path)[0]
                self.nails = nailcache.get_nails(folderPath, self.nailSz, self.env)
            except FileNotFoundError:
                self.log_error("No thumbnail file for size {}".format(self.nailSz))
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
                photo = nailcache.get_loose_file(ent.path, self.nailSz)
                if photo is None:
                    self.log_error(str(e)) #no thumbnail for this file
        else:
            # no log when this fails because we've already said the xpng file is missing
            photo = nailcache.get_loose_file(ent.path, self.nailSz)

        # if still no image, try to create thumbnail on the fly
        if photo is None:
            try:
                im = Image.open(ent.path)
                im = pic.fix_image_orientation(im)
                im.thumbnail((self.nailSz, self.nailSz))
                photo = ImageTk.PhotoImage(im)
                # add to loose file cache
                nailcache.add_loose_file(ent.path, self.nailSz, photo)
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
        self.tilesOrder.append(tile)
        self.tilesByName[tile.name] = tile
        if tile.id:
            if tile.id in self.tiles:
                # duplicate groovy ID
                tile.set_error(pic.DUP)
                self.log_error("Duplicate ID: {}".format(tile.name))
                otherTile = self.tiles[tile.id]
                if not otherTile.is_error(pic.DUP):
                    otherTile.set_error(pic.DUP)
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

    # remove a tile
    def remove_tile(self, tile):
        try:
            if tile.id:
                del self.tiles[tile.id]
        except KeyError:
            self.log_error("Error removing {}, id={} not in tiles".format(tile.name, tile.id))
        try:
            self.tilesOrder.remove(tile)
        except ValueError:
            self.log_error("Error removing {}, not in tilesOrder".format(tile.name))
        try:
            del self.tilesByName[tile.name]
        except ValueError:
            self.log_error("Error removing {}, not in tilesByName".format(tile.name))
        if tile is self.lastTileClicked:
            self.lastTileClicked = None
        tile.erase(self.canvas)
