# shoebox.medit

import os, json
from tkinter import *
from tkinter import ttk, filedialog
from tkit.loghelper import LogHelper

instances = []
nextInstNum = 1

class Medit(LogHelper):
    def __init__(self):
        self.env = {}
        LogHelper.__init__(self, self.env)
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1

        # create top level window
        self.top = Toplevel()
        self.myName = "Medit {:d}".format(self.instNum)
        self.top.title(self.myName)
        self.top.bind('<Destroy>', self.on_destroy)

        # create top button bar
        self.topBar = Frame(self.top)
        self.topBar.grid(column=0, row=0, sticky=(N, W, E))
        self.loadButton = ttk.Button(self.topBar, text="Load", command=self.do_load)
        self.loadButton.pack(side=LEFT)
        self.enable_buttons(False)

        # style for error messages (status bar)
        s = ttk.Style()
        s.configure('Error.TLabel', foreground='red')

        # create status bar
        self.statusBar = Frame(self.top)
        self.statusBar.grid(column=0, row=1, sticky=(N, W, E))
        self.statusLabel = ttk.Label(self.statusBar, text="")
        self.statusLabel.pack(side=LEFT, fill=X, expand=True)
        self.logButton = ttk.Button(self.statusBar, text="Log", command=self.do_log)
        self.logButton.pack(side=RIGHT)

        # create tree view for meta changes
        self.treeFrame = Frame(self.top)
        self.treeScroll = Scrollbar(self.treeFrame)
        self.treeScroll.pack(side=RIGHT, fill=Y)
        self.tree = ttk.Treeview(self.treeFrame, columns=('prop', 'val', 'ts', 'userId'))
        self.tree.column('#0', width=100, stretch=False)
        self.tree.heading('#0', text="ID")
        self.tree.column('prop', width=100, stretch=False)
        self.tree.heading('prop', text="Property")
        self.tree.column('val', width=100, stretch=True)
        self.tree.heading('val', text="Value")
        self.tree.column('ts', width=100, stretch=False)
        self.tree.heading('ts', text="Date/Time")
        self.tree.column('userId', width=100, stretch=False)
        self.tree.heading('userId', text="User")
        self.tree.pack(side=RIGHT, fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.configure(yscrollcommand=self.treeScroll.set)
        self.treeScroll.configure(command=self.tree.yview)
        self.treeFrame.grid(column=0, row=2, sticky=(N,W,E,S))
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(2, weight=1)

        # tree stuff
        #self.tree.tag_configure('noncanon', background='cyan')
        #self.tree.tag_configure('error', background='orange')
        #self.tree.tag_configure('childerror', background='tan')
        #self.treeItems = {} #tree iid to file object

        self.journalFile = None
        self.nMetaChgs = 0
        self.lastError = ""
        self.set_status_default_or_error()
        instances.append(self)

    # called when my top-level window is closed
    # this is the easiest and most common way to destroy Medit,
    # and includes the case where the entire shoebox application is shut down
    def on_destroy(self, ev):
        self.top = None
        self.destroy()

    # destroy and clean up this Medit
    # in Python you don't really destroy objects, you just remove all references to them
    # so this function removes all known references then closes the top level window
    # note this will result in a second call from the on_destroy event handler; that's ok
    def destroy(self):
        if self in instances:
            instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    # Medit destructor
    def __del__(self):
        self.destroy() #probably already called

    # set status to specified string
    def set_status(self, msg, error=False):
        self.statusLabel.configure(text=msg, style="Error.TLabel" if error else "TLabel")
        self.top.update_idletasks()

    # set status to default message
    def set_status_default(self):
        if self.journalFile is None:
            self.set_status("Load a journal file")
        else:
            self.set_status("Ready ({:d} meta changes)".format(self.nMetaChgs))

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
    # for info optionally show in status and log it
    def log_error(self, msg):
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

    # enable/disable buttons
    def enable_buttons(self, enable=True):
        pass

    # when Log button clicked
    def do_log(self):
        self.open_log_window("Log - {}".format(self.myName))

   # when load button is clicked
    def do_load(self):
        journalFile = filedialog.askopenfilename(title="{} - Load metajournal".format(self.myName))
        with open(journalFile, mode='r', encoding='UTF-8') as f:
            for line in f:
                metaChg = json.loads(line)
                if 'rating' in metaChg:
                    iid = self.tree.insert('', 'end', text=metaChg['id'],
                                           values=('rating', metaChg['rating'], metaChg['ts'], metaChg['userId']))
                if 'caption' in metaChg:
                    iid = self.tree.insert('', 'end', text=metaChg['id'],
                                           values=('caption', metaChg['caption'], metaChg['ts'], metaChg['userId']))

    # when user clicks tree item
    def on_tree_select(self, event):
        sel = self.tree.selection()
        print("you clicked", sel)

