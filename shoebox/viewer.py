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

class Viewer(LogHelper, WidgetHelper):
    def __init__(self, px):
        self.env = {}
        LogHelper.__init__(self, self.env)
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1

        self.px = px

        # create top level window
        self.top = Toplevel()
        self.myName = "Viewer {:d}".format(self.instNum)
        self.top.title(self.myName)
        self.top.bind('<Destroy>', self.on_destroy)

        # create top button bar
        self.topBar = Frame(self.top)
        self.topBar.grid(column=0, row=0, sticky=(N,W,E))
        self.prevButton = ttk.Button(self.topBar, text="<<", command=self.do_prev)
        self.prevButton.pack(side=LEFT)
        self.nextButton = ttk.Button(self.topBar, text=">>", command=self.do_next)
        self.nextButton.pack(side=LEFT)
        self.splitButton = ttk.Button(self.topBar, text="Split", command=self.do_split)
        self.splitButton.pack(side=RIGHT)
        self.enable_buttons(True)

        # create status bar
        self.statusBar = Frame(self.top)
        self.statusBar.grid(column=0, row=1, sticky=(N,W,E))
        self.statusLabel = ttk.Label(self.statusBar, text="")
        self.statusLabel.pack(side=LEFT, fill=X, expand=True)
        self.logButton = ttk.Button(self.statusBar, text="Log", command=self.do_log)
        self.logButton.pack(side=RIGHT)

        # styles
        s = ttk.Style()
        # style for error messages (status bar)
        s.configure('Error.TLabel', foreground='red')
        # style for prev/next button hitting limit
        s.configure('Stop.TButton', background='red')

        # create canvas
        self.canvas = Canvas(self.top, background="black", width=800, height=800)
        self.canvas.grid(column=0, row=2, sticky=(N,W,E,S))
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(2, weight=1)

        # canvas stuff
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        self.canvas.bind('<MouseWheel>', self.on_canvas_wheel)
        self.canvas.bind('<Double-Button-1>', self.on_canvas_doubleclick)
        self.canvas.bind('<B1-Motion>', self.on_canvas_motion)
        self.canvas.bind('<ButtonRelease>', self.on_canvas_release)

        self.lastError = ""
        self.index = 0
        self.fullImg = None
        self.cropImg = None
        self.tkPhoto = None
        self.imgItem = None
        self.zoom = 1.0
        self.panx = 0
        self.pany = 0
        self.dragging = False
        self.dragStart = None
        self.set_status_default_or_error()
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
        if self.px:
            self.px.viewer = None
            self.px = None
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

    def set_status(self, msg, error=False):
        """set status to specified string"""
        self.statusLabel.configure(text=msg, style="Error.TLabel" if error else "TLabel")
        self.top.update_idletasks()

    def set_status_default(self):
        """set status to default message"""
        self.set_status("Connected to {}".format(self.px.myName))

    def set_status_default_or_error(self):
        """set status to default message or error"""
        if self.lastError:
            self.set_status(self.lastError, True)
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

    def do_log(self):
        """when Log button clicked"""
        self.open_log_window("Log - {}".format(self.myName))

    def enable_buttons(self, enable=True):
        """enable/disable buttons"""
        self.enable_widget(self.splitButton, enable)
        self.enable_widget(self.prevButton, enable)
        self.enable_widget(self.nextButton, enable)

    def do_split(self):
        """when Split button is pressed"""
        pass

    def on_canvas_resize(self, event):
        """when user resizes the window"""
        self.draw_image()

    def set_picture(self, index):
        self.index = index
        tile = self.px.tilesOrder[index]
        path = os.path.join(self.px.curFolder.path, tile.name)
        f = open(path, "rb")
        self.fullImg = Image.open(f)
        self.fullImg.load()
        f.close()
        self.fullImg = pic.fix_image_orientation(self.fullImg)
        self.zoom = 1.0
        self.draw_image()
        self.set_prev_next_stop()
        self.set_status(tile.name)

    def draw_image(self):
        fw, fh = self.fullImg.size
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw > 1 and ch > 1:
            w = cw
            h = fh * (cw / fw)
            if h > ch:
                h = ch
                w = fw * (ch / fh)
            zw = w * self.zoom
            zh = h * self.zoom
            mx = zw / 2.0
            my = zh / 2.0
            mw = cw / 2.0
            mh = ch / 2.0
            x0 = min(max(mx - mw + self.panx, 0), max(zw-cw, 0))
            y0 = min(max(my - mh + self.pany, 0), max(zh-ch, 0))
            bb = (int(x0), int(y0), int(x0+cw), int(y0+ch))
            self.cropImg = self.fullImg.resize((int(zw), int(zh))).crop(bb)
            self.tkPhoto = ImageTk.PhotoImage(self.cropImg)
            if self.imgItem is not None:
                self.canvas.delete(self.imgItem)
            self.imgItem = self.canvas.create_image(0, 0, image=self.tkPhoto, anchor=NW)

    def on_canvas_wheel(self, event):
        zbefore = self.zoom
        self.zoom += event.delta / 2000.0
        if self.zoom <= 0:
            self.zoom = zbefore
        else:
            self.panx *= self.zoom / zbefore
            self.pany *= self.zoom / zbefore
            self.draw_image()

    def on_canvas_doubleclick(self, event):
        self.zoom = 1.0
        self.panx = 0
        self.pany = 0
        self.draw_image()

    def on_canvas_motion(self, event):
        """when mouse moved with button down"""
        if not self.dragging:
            self.dragging = True
            self.dragStart = (self.panx + event.x, self.pany + event.y)
            self.canvas.configure(cursor="fleur")
        else:
            self.panx = self.dragStart[0] - event.x
            self.pany = self.dragStart[1] - event.y
            self.draw_image()

    def on_canvas_release(self, event):
        """when mouse button released"""
        self.dragging = False
        self.canvas.configure(cursor="")

    def do_prev(self):
        """when Prev button clicked"""
        if self.index > 0:
            for i in range(self.index-1, -1, -1):
                if isinstance(self.px.tilesOrder[i], PxTilePic):
                    self.set_picture(i)
                    self.px.goto_index(i, len(selectColors))
                    return
        self.set_prev_next_stop(prev=True)

    def do_next(self):
        """when Next button clickec"""
        if self.index < len(self.px.tilesOrder) - 1:
            for i in range(self.index+1, len(self.px.tilesOrder), 1):
                if isinstance(self.px.tilesOrder[i], PxTilePic):
                    self.set_picture(i)
                    self.px.goto_index(i, len(selectColors))
                    return
        self.set_prev_next_stop(next=True)

    def set_prev_next_stop(self, prev=False, next=False):
        self.prevButton.configure(style="Stop.TButton" if prev else "TButton")
        self.nextButton.configure(style="Stop.TButton" if next else "TButton")
