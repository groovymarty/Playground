# shoebox.viewer

import os
from tkinter import *
from tkinter import ttk
from PIL import Image
import ImageTk
from shoebox import pic
from tkit.loghelper import LogHelper
from tkit.widgethelper import WidgetHelper
from tkit import tkit

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
        self.splitButton = ttk.Button(self.topBar, text="Split", command=self.do_split)
        self.splitButton.pack(side=LEFT)
        self.enable_buttons(True)

        # create status bar
        self.statusBar = Frame(self.top)
        self.statusBar.grid(column=0, row=1, sticky=(N,W,E))
        self.statusLabel = ttk.Label(self.statusBar, text="")
        self.statusLabel.pack(side=LEFT, fill=X, expand=True)
        self.logButton = ttk.Button(self.statusBar, text="Log", command=self.do_log)
        self.logButton.pack(side=RIGHT)

        # created paned window for split view
        self.panedWin = PanedWindow(self.top, orient=HORIZONTAL, width=800, height=800, sashwidth=5, sashrelief=GROOVE)
        self.panedWin.grid(column=0, row=2, sticky=(N,W,E,S))
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(2, weight=1)

        # styles
        s = ttk.Style()
        # style for error messages (status bar)
        s.configure('Error.TLabel', foreground='red')

        # create canvas
        self.canvas = Canvas(self.panedWin, background="black")
        self.canvas.pack(side=RIGHT, fill=BOTH, expand=True)
        self.panedWin.add(self.canvas)

        # canvas stuff
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        self.canvas.bind('<MouseWheel>', self.on_canvas_wheel)
        self.canvas.bind('<Button-1>', self.on_canvas_click)

        self.lastError = ""
        self.index = 0
        self.fullImg = None
        self.cropImg = None
        self.tkPhoto = None
        self.imgItem = None
        self.zoom = 1.0
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

    def do_split(self):
        """when Split button is pressed"""
        pass

    def on_canvas_resize(self, event):
        """when user resizes the window"""
        self.draw_image()

    def set_picture(self, tile, index):
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
            self.cropImg = self.fullImg.resize((int(zw), int(zh))).crop((0, 0, int(cw), int(ch)))
            self.tkPhoto = ImageTk.PhotoImage(self.cropImg)
            if self.imgItem is not None:
                self.canvas.delete(self.imgItem)
            self.imgItem = self.canvas.create_image(0, 0, image=self.tkPhoto, anchor=NW)

    def on_canvas_wheel(self, event):
        self.zoom += event.delta / 3000.0
        self.draw_image()

    def on_canvas_click(self, event):
        self.zoom = 1.0
        self.draw_image()
