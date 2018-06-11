# shoebox.viewer

import os
from tkinter import *
from tkinter import ttk
from PIL import Image
import ImageTk
from shoebox import pic
from shoebox.pxtile import PxTilePic, selectColors
from tkit.loghelper import LogHelper
from tkit.widgethelper import WidgetHelper

instances = []
nextInstNum = 1

class Pane:
    def __init__(self, viewer, side):
        self.viewer = viewer
        self.owner = viewer.owner
        self.side = side
        self.selectColor = len(selectColors)
        if side == RIGHT:
            self.selectColor -= 1

        self.prevButton = ttk.Button(self.viewer.topBar, text="<<", command=self.do_prev)
        self.nextButton = ttk.Button(self.viewer.topBar, text=">>", command=self.do_next)
        if side == LEFT:
            self.prevButton.pack(side=side)
            self.nextButton.pack(side=side)
        else:
            self.nextButton.pack(side=side)
            self.prevButton.pack(side=side)

        self.statusLabel = ttk.Label(self.viewer.statusBar, text="")
        self.statusLabel.pack(side=side)
        if side == LEFT:
            self.statusLabel.pack(expand=True, fill=X)

        # create canvas
        self.canvas = Canvas(self.viewer.canvasFrame, background="black",
                             highlightthickness=3, highlightbackground="black",
                             highlightcolor=selectColors[self.selectColor])
        self.canvas.pack(side=side, fill=BOTH, expand=True)

        # canvas stuff
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        self.canvas.bind('<MouseWheel>', self.on_canvas_wheel)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<Double-Button-1>', self.on_canvas_doubleclick)
        self.canvas.bind('<B1-Motion>', self.on_canvas_motion)
        self.canvas.bind('<ButtonRelease>', self.on_canvas_release)

        self.index = 0
        self.path = None
        self.fullImg = None
        self.resizeImg = None
        self.lastResize = (0, 0)
        self.cropImg = None
        self.tkPhoto = None
        self.imgItem = None
        self.zoomAndPan = {}
        self.dragging = False
        self.dragStart = None

    def on_canvas_resize(self, event):
        """when user resizes the window"""
        self.draw_image()

    def on_canvas_wheel(self, event):
        zoom, panx, pany = self.get_zoom_and_pan()
        zbefore = zoom
        zoom += event.delta / 2000.0
        if zoom > 0:
            panx *= zoom / zbefore
            pany *= zoom / zbefore
            self.zoomAndPan[self.path] = (zoom, panx, pany)
            self.draw_image()

    def on_canvas_click(self, event):
        self.set_focus()
        self.owner.goto_index(self.index, self.selectColor)

    def on_canvas_doubleclick(self, event):
        self.zoomAndPan[self.path] = (1.0, 0, 0)
        self.draw_image()

    def on_canvas_motion(self, event):
        """when mouse moved with button down"""
        zoom, panx, pany = self.get_zoom_and_pan()
        if not self.dragging:
            self.dragging = True
            self.dragStart = (panx + event.x, pany + event.y)
            self.canvas.configure(cursor="fleur")
        else:
            panx = self.dragStart[0] - event.x
            pany = self.dragStart[1] - event.y
            self.zoomAndPan[self.path] = (zoom, panx, pany)
            self.draw_image()

    def on_canvas_release(self, event):
        """when mouse button released"""
        self.dragging = False
        self.canvas.configure(cursor="")

    def set_picture(self, index):
        self.index = index
        tile = self.owner.tilesOrder[index]
        self.path = self.owner.get_tile_path(tile)
        try:
            if self.path:
                try:
                    f = open(self.path, "rb")
                    self.fullImg = Image.open(f)
                    self.fullImg.load()
                    f.close()
                except FileNotFoundError:
                    raise RuntimeError("File not found: {}".format(self.path))
            else:
                raise RuntimeError("Path not found: {}".format(tile.id if 'id' in tile else "None"))

            self.fullImg = pic.fix_image_orientation(self.fullImg)
            self.resizeImg = None
            self.lastResize = (0, 0)
            self.draw_image()
            self.set_prev_next_stop()
            self.statusLabel.configure(text=tile.name)
            self.set_focus()
        except RuntimeError as e:
            self.statusLabel.configure(text=str(e))
            self.viewer.log_error(str(e))
            self.fullImg = None

    def draw_image(self):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw > 1 and ch > 1 and self.fullImg is not None:
            fw, fh = self.fullImg.size
            w = cw
            h = fh * (cw / fw)
            if h > ch:
                h = ch
                w = fw * (ch / fh)
            zoom, panx, pany = self.get_zoom_and_pan()
            zw = w * zoom
            zh = h * zoom
            mx = zw / 2.0
            my = zh / 2.0
            mw = cw / 2.0
            mh = ch / 2.0
            panx = min(max(panx, -mx-mw), mx+mw)
            pany = min(max(pany, -my-mh), my+mh)
            self.zoomAndPan[self.path] = (zoom, panx, pany)
            x0 = mx - mw + panx
            y0 = my - mh + pany
            bb = (int(x0), int(y0), int(x0+cw), int(y0+ch))
            size = ((int(zw), int(zh)))
            if self.resizeImg is None or size != self.lastResize:
                self.resizeImg = self.fullImg.resize(size)
                self.lastResize = size
            self.cropImg = self.resizeImg.crop(bb)
            self.tkPhoto = ImageTk.PhotoImage(self.cropImg)
            if self.imgItem is not None:
                self.canvas.delete(self.imgItem)
            self.imgItem = self.canvas.create_image(0, 0, image=self.tkPhoto, anchor=NW)

    def do_prev(self):
        """when Prev button clicked"""
        self.set_focus()
        if self.index > 0:
            for i in range(self.index-1, -1, -1):
                if isinstance(self.owner.tilesOrder[i], PxTilePic):
                    self.set_picture(i)
                    self.owner.goto_index(i, self.selectColor)
                    return
        self.set_prev_next_stop(prev=True)

    def do_next(self):
        """when Next button clickec"""
        self.set_focus()
        if self.index < len(self.owner.tilesOrder) - 1:
            for i in range(self.index+1, len(self.owner.tilesOrder), 1):
                if isinstance(self.owner.tilesOrder[i], PxTilePic):
                    self.set_picture(i)
                    self.owner.goto_index(i, self.selectColor)
                    return
        self.set_prev_next_stop(next=True)

    def set_prev_next_stop(self, prev=False, next=False):
        self.prevButton.configure(style="Stop.TButton" if prev else "TButton")
        self.nextButton.configure(style="Stop.TButton" if next else "TButton")

    def set_focus(self):
        self.canvas.focus_set()
        self.viewer.focusSide = self.side

    def get_zoom_and_pan(self):
        try:
            return self.zoomAndPan[self.path]
        except KeyError:
            return (1.0, 0, 0)

class Viewer(LogHelper, WidgetHelper):
    def __init__(self, owner):
        # owner is px or cx
        self.env = {}
        LogHelper.__init__(self, self.env)
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1

        self.owner = owner

        # create top level window
        self.top = Toplevel()
        self.top.geometry("800x800")
        self.myName = "Viewer {:d}".format(self.instNum)
        self.top.title(self.myName)
        self.top.bind('<Destroy>', self.on_destroy)
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(2, weight=1)

        # create top button bar
        self.topBar = Frame(self.top)
        self.topBar.grid(column=0, row=0, sticky=(N,W,E))
        self.splitButton = ttk.Button(self.topBar, text="Split", command=self.do_split)
        self.splitButton.pack(side=RIGHT)

        # create status bar
        self.statusBar = Frame(self.top)
        self.statusBar.grid(column=0, row=1, sticky=(N,W,E))
        self.logButton = ttk.Button(self.statusBar, text="Log", command=self.do_log)
        self.logButton.pack(side=RIGHT)

        # styles
        s = ttk.Style()
        # style for error messages (status bar)
        s.configure('Error.TLabel', foreground='red')
        # style for prev/next button hitting limit
        s.configure('Stop.TButton', background='red')

        # create left pane
        self.canvasFrame = Frame(self.top)
        self.canvasFrame.grid(column=0, row=2, sticky=(N,W,E,S))
        self.lpane = Pane(self, LEFT)
        self.rpane = None
        self.hsplit = False
        self.focusSide = LEFT
        instances.append(self)

    def on_destroy(self, ev):
        """called when my top-level window is closed
        this is the easiest and most common way to destroy Viewer,
        and includes the case where the entire shoebox application is shut down
        """
        self.top = None
        self.destroy()

    def destroy(self):
        """destroy and clean up this Viewer
        in Python you don't really destroy objects, you just remove all references to them
        so this function removes all known references then closes the top level window
        note this will result in a second call from the on_destroy event handler; that's ok
        """
        if self.owner:
            self.owner.viewer = None
            self.owner = None
        self.close_log_windows()
        if self in instances:
            instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    def __del__(self):
        """Viewer destructor"""
        self.destroy() #probably already called
        LogHelper.__del__(self)

    def do_log(self):
        """when Log button clicked"""
        self.open_log_window("Log - {}".format(self.myName))

    def do_split(self):
        """when Split button is pressed"""
        if self.rpane is None:
            self.rpane = Pane(self, RIGHT)
            self.rpane.set_picture(self.lpane.index)
        else:
            self.hsplit = not self.hsplit
        if self.hsplit:
            self.lpane.canvas.pack(side=TOP, fill=BOTH, expand=True)
            self.rpane.canvas.pack(side=TOP, fill=BOTH, expand=True)
            self.splitButton.configure(text="Vertical")
        else:
            self.lpane.canvas.pack(side=LEFT, fill=BOTH, expand=True)
            self.rpane.canvas.pack(side=LEFT, fill=BOTH, expand=True)
            self.splitButton.configure(text="Horizontal")

    def set_picture(self, index):
        if self.rpane is not None and self.focusSide == RIGHT:
            self.rpane.set_picture(index)
        else:
            self.lpane.set_picture(index)
