# tkit.loghelper

import time
from tkinter import *
from tkinter import ttk

class LogWindow:
    def __init__(self, title, instances):
        self.instances = instances
        self.top = Toplevel()
        self.top.title(title)
        self.top.bind('<Destroy>', self.on_destroy)
        self.scroll = Scrollbar(self.top)
        self.scroll.pack(side=RIGHT, fill=Y)
        self.text = Text(self.top)
        self.text.pack(fill=BOTH, expand=True)
        self.text.configure(font=("helvetica", 10))
        self.text.configure(yscrollcommand=self.scroll.set)
        self.scroll.configure(command=self.text.yview)
        self.instances.append(self)

    def on_destroy(self, ev):
        self.top = None
        self.destroy()

    def destroy(self):
        if self in self.instances:
            self.instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    def __del__(self):
        self.destroy()

    def add_entry(self, ent):
        (ts, kind, msg) = ent
        t = time.asctime(time.localtime(ts))
        self.text.insert(END, "{} {}: {}\n".format(t, kind, msg))

    def clear(self):
        self.text.delete("1.0", END)

class LogHelper:
    def __init__(self):
        self.logBuf = []
        self.logWindows = []

    def __del__(self):
        for win in list(self.logWindows):
            win.destroy()

    def clear_log(self):
        self.logBuf.clear()
        for win in self.logWindows:
            win.clear()

    def log(self, kind, msg):
        ent = (time.time(), kind, msg)
        self.logBuf.append(ent)
        for win in self.logWindows:
            win.add_entry(ent)

    def log_info(self, msg):
        self.log("Info", msg)

    def log_error(self, msg):
        self.log("Error", msg)

    def open_log_window(self, title):
        win = LogWindow(title, self.logWindows)
        for ent in self.logBuf:
            win.add_entry(ent)
