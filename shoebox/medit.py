# shoebox.medit

import os, json
from tkinter import *
from tkinter import ttk, filedialog
from tkit.loghelper import LogHelper
from tkit.widgethelper import WidgetHelper
from tkit import environ
from datetime import datetime
from shoebox import px, pic

instances = []
nextInstNum = 1

class MetaChg:
    def __init__(self, id, prop, val, ts, userId):
        self.id = id
        self.iid = None  # see populate_tree()
        self.prop = prop
        self.val = val
        self.oldval = ""
        self.ts = ts
        self.userId = userId
        self.status = ""
        self.shadowed = False
        self.applied = False
        self.rejected = False
        self.softSelected = False
        self.parts = pic.parse_file(id)
        if not self.parts:
            raise RuntimeError("Bad ID in journal entry: {}".format(id))
        try:
            self.formattedTs = datetime.utcfromtimestamp(self.ts / 1e3).astimezone()\
                .strftime("%a %b %d %Y  %I:%M %p")
        except Exception as e:
            raise RuntimeError("Bad timestamp in journal entry: {}, {}".format(ts, str(e)))

    def apply(self):
        if not self.applied and not self.shadowed:
            # TODO apply it!
            self.applied = True
            self.rejected = False
            return True
        else:
            return False

    def reject(self):
        if not self.rejected and not self.shadowed:
            if self.applied:
                self.undo()
            self.rejected = True
            return True
        else:
            return False

    def undo(self):
        if self.applied or self.rejected:
            if self.applied:
                pass  # unapply it!
            self.applied = False
            self.rejected = False
            return True
        else:
            return False

class Medit(LogHelper, WidgetHelper):
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
        self.applyButton = ttk.Button(self.topBar, text="Apply", command=self.do_apply)
        self.applyButton.pack(side=LEFT)
        self.rejectButton = ttk.Button(self.topBar, text="Reject", command=self.do_reject)
        self.rejectButton.pack(side=LEFT)
        self.undoButton = ttk.Button(self.topBar, text="Undo", command=self.do_undo)
        self.undoButton.pack(side=LEFT)

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
        self.tree = ttk.Treeview(self.treeFrame, columns=('prop', 'val', 'was', 'dt', 'user', 'status'), height=36)
        self.tree.column('#0', width=100, stretch=False)
        self.tree.heading('#0', text="ID")
        self.tree.column('prop', width=100, stretch=False)
        self.tree.heading('prop', text="Property")
        self.tree.column('val', width=250, stretch=True)
        self.tree.heading('val', text="Value")
        self.tree.column('was', width=100, stretch=False)
        self.tree.heading('was', text="Was")
        self.tree.column('dt', width=180, stretch=False)
        self.tree.heading('dt', text="Date/Time")
        self.tree.column('user', width=100, stretch=False)
        self.tree.heading('user', text="User")
        self.tree.column('status', width=100, stretch=False)
        self.tree.heading('status', text="Status")
        self.tree.pack(side=RIGHT, fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.configure(yscrollcommand=self.treeScroll.set)
        self.treeScroll.configure(command=self.tree.yview)
        self.treeFrame.grid(column=0, row=2, sticky=(N,W,E,S))
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(2, weight=1)

        # tree stuff
        self.tree.tag_configure('shadowed', background='gray')
        self.tree.tag_configure('applied', background='lime')
        self.tree.tag_configure('rejected', background='pink')
        self.tree.tag_configure('softsel', foreground='blue', font=('Helvetica', 9, 'italic'))

        self.journalFile = None
        self.loaded = False
        self.mcOrder = []  # meta changes in sorted order
        self.treeItems = {}  # tree id to meta change
        self.lastError = ""
        self.pxInstNum = None
        self.set_status_default_or_error()
        self.update_buttons()
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
        self.close_log_windows()
        if self in instances:
            instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    # Medit destructor
    def __del__(self):
        self.destroy() #probably already called
        LogHelper.__del__(self)

    # set status to specified string
    def set_status(self, msg, error=False):
        self.statusLabel.configure(text=msg, style="Error.TLabel" if error else "TLabel")
        self.top.update_idletasks()

    # set status to default message
    def set_status_default(self):
        if not self.loaded:
            self.set_status("Load a journal file")
        elif self.pxInstNum is not None:
            self.set_status("Using Px {:d}, {:d} meta changes". format(self.pxInstNum, len(self.treeItems)))
        else:
            self.set_status("Ready ({:d} meta changes)".format(len(self.treeItems)))

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
    def update_buttons(self):
        anySel = len(self.get_selected_items())
        self.enable_widget(self.loadButton, not self.loaded)
        self.enable_widget(self.applyButton, self.loaded and anySel)
        self.enable_widget(self.rejectButton, self.loaded and anySel)
        self.enable_widget(self.undoButton, self.loaded and anySel)

    # when Log button clicked
    def do_log(self):
        self.open_log_window("Log - {}".format(self.myName))

   # when load button is clicked
    def do_load(self):
        self.journalFile = filedialog.askopenfilename(title="{} - Load Journal".format(self.myName))
        if self.journalFile:
            try:
                with open(self.journalFile, mode='r', encoding='UTF-8') as f:
                    self.mcOrder = []
                    lineNum = 0
                    for line in f:
                        lineNum += 1
                        ent = json.loads(line)
                        try:
                            id = ent['id']
                            ts = ent['ts']
                            userId = ent['userId']
                        except KeyError as e:
                            self.log_error("Line {}: Journal entry lacks required field: {}".format(lineNum, str(e)))
                            continue
                        # create a separate MetaChg object for each property changed
                        try:
                            if 'rating' in ent:
                                self.mcOrder.append(MetaChg(id, 'rating', ent['rating'], ts, userId))
                            if 'caption' in ent:
                                self.mcOrder.append(MetaChg(id, 'caption', ent['caption'], ts, userId))
                        except RuntimeError as e:
                            self.log_error("Line {}: {}".format(lineNum, str(e)))

                # sort by ID then property then timestamp
                self.mcOrder.sort(key=lambda mc: (mc.parts.parent, mc.parts.child, mc.parts.sortNum, mc.prop, mc.ts))
                self.clear_tree()
                self.populate_tree(self.mcOrder)
                self.update_status_all()
                self.update_tree_all()
                self.loaded = True
            except Exception as e:
                self.log_error("Error reading {}: {}", self.journalFile, str(e))
        self.set_status_default_or_error()
        self.update_buttons()

    # clear all tree entries
    def clear_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.treeItems = {}
        self.loaded = False

    # populate tree
    def populate_tree(self, metaChgs):
        for mc in metaChgs:
            iid = self.tree.insert('', 'end',
                                   text=mc.id,
                                   values=(mc.prop, mc.val, mc.oldval, mc.formattedTs, mc.userId, mc.status))
            self.treeItems[iid] = mc
            mc.iid = iid

    # update status for all meta changes
    def update_status_all(self):
        prevMc = None
        for mc in self.mcOrder:
            status = "Pending"
            mc.shadowed = False
            if mc.rejected:
                status = "Rejected"
            elif mc.applied:
                status = "Applied"

            # if same ID and property as previous entry, and not rejected, previous is shadowed
            if prevMc and prevMc.id == mc.id and prevMc.prop == mc.prop and not mc.rejected:
                prevMc.shadowed = True
                prevMc.applied = False
                prevMc.rejected = False
                prevMc.status = "Shadowed"
            mc.status = status
            prevMc = mc

    # update all tree items
    def update_tree_all(self):
        for iid in self.treeItems:
            self.update_tree_item(iid)

    # update tree item
    def update_tree_item(self, iid):
        mc = self.treeItems[iid]
        tags = []
        if mc.shadowed:
            tags.append("shadowed")
        elif mc.rejected:
            tags.append("rejected")
        elif mc.applied:
            tags.append("applied")
        if mc.softSelected:
            tags.append("softsel")

        self.tree.set(iid, 'status', mc.status)
        self.tree.item(iid, tags=tags)

    # when user clicks tree item
    def on_tree_select(self, event):
        self.deselect_shadowed_items()
        self.update_buttons()
        sel = self.tree.selection()
        if len(sel):
            self.soft_deselect_all()
            pxInst = px.get_instance(self.pxInstNum)
            if pxInst:
                oldInstNum = self.pxInstNum
                self.pxInstNum = pxInst.instNum
                if pxInst.instNum != oldInstNum and oldInstNum is not None:
                    self.set_status("Can't find Px {:d}, switching to Px {:d}".format(oldInstNum, pxInst.instNum))
                else:
                    self.set_status_default()
                pxInst.goto(self.treeItems[sel[0]].id)
            else:
                self.set_status("No Px found, please create one")
                self.pxInstNum = None

    # clear shadowed items from selection
    def deselect_shadowed_items(self):
        for iid in self.tree.selection():
            if self.treeItems[iid].shadowed:
                self.tree.selection_remove(iid)

    # get selected items
    def get_selected_items(self):
        sel = self.tree.selection()
        if len(sel):
            return [self.treeItems[iid] for iid in sel]
        else:
            return [mc for mc in self.mcOrder if mc.softSelected]

    # clear soft selections
    def soft_deselect_all(self):
        for iid, mc in self.treeItems.items():
            if mc.softSelected:
                mc.softSelected = False
                self.update_tree_item(iid)

    # when apply clicked
    def do_apply(self):
        n = 0
        for mc in self.get_selected_items():
            self.tree.selection_remove(mc.iid)
            mc.softSelected = True
            if mc.apply():
                n += 1
        self.update_status_all()
        self.update_tree_all()
        self.set_status("{} items applied".format(n))
        self.update_buttons()

    # when reject clicked
    def do_reject(self):
        n = 0
        for mc in self.get_selected_items():
            self.tree.selection_remove(mc.iid)
            mc.softSelected = True
            if mc.reject():
                n += 1
        self.update_status_all()
        self.update_tree_all()
        self.set_status("{} items rejected".format(n))
        self.update_buttons()

    # when undo clicked
    def do_undo(self):
        n = 0
        for mc in self.get_selected_items():
            self.tree.selection_remove(mc.iid)
            mc.softSelected = True
            if mc.undo():
                n += 1
        self.update_status_all()
        self.update_tree_all()
        self.set_status("{} items undone".format(n))
        self.update_buttons()
