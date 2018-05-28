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
        self.canvasWidth = 0
        self.canvas.bind('<Configure>', self.on_canvas_resize)

        self.lastError = ""
        self.curFolder = None
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
        if self.canvas.winfo_width() != self.canvasWidth:
            self.canvasWidth = self.canvas.winfo_width()

    def set_picture(self, tile):
        print("setting {}".format(tile.name))
