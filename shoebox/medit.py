# shoebox.medit

import os, json
from tkinter import *
from tkinter import ttk, filedialog
from tkit.loghelper import LogHelper
from tkit.widgethelper import WidgetHelper
from tkit import environ
from datetime import datetime
from shoebox import px, pic, finder, metacache

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

    def apply(self, env=None):
        if not self.applied and not self.shadowed:
            folderPath = finder.find_folder(pic.get_folder_id(self.parts))
            if folderPath:
                md = metacache.get_meta_dict(folderPath, env)
                if md:
                    self.oldval = md.get_value(self.id, self.prop)
                    md.apply_meta(self.id, {self.prop: self.val})
                    self.applied = True
                    self.rejected = False
                    return True
                else:
                    environ.log_error(env, "Can't find meta dictionary for {}".format(self.id))
                    return False
            else:
                environ.log_error(env, "Can't find folder for {}".format(self.id))
                return False
        else:
            return False

    def reject(self, env=None):
        if not self.rejected and not self.shadowed:
            if self.applied:
                self.undo(env)
            self.rejected = True
            return True
        else:
            return False

    def undo(self, env=None):
        if self.applied or self.rejected:
            if self.applied:
                folderPath = finder.find_folder(pic.get_folder_id(self.parts))
                if folderPath:
                    md = metacache.get_meta_dict(folderPath, env)
                    if md:
                        md.apply_meta(self.id, {self.prop: self.oldval})
                        self.oldval = ""
            self.applied = False
            self.rejected = False
            return True
        else:
            return False

    def mark_as_is(self, env=None):
        folderPath = finder.find_folder(pic.get_folder_id(self.parts))
        if folderPath:
            md = metacache.get_meta_dict(folderPath, env)
            if md:
                if md.get_value(self.id, self.prop) == self.val:
                    self.applied = True
                    self.rejected = False
                else:
                    self.applied = False
                    self.rejected = True
                return True
            else:
                environ.log_error(env, "Can't find meta dictionary for {}".format(self.id))
                return False
        else:
            environ.log_error(env, "Can't find folder for {}".format(self.id))
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
        self.applyButton = ttk.Button(self.topBar, text="Apply (A)", command=self.do_apply)
        self.applyButton.pack(side=LEFT)
        self.rejectButton = ttk.Button(self.topBar, text="Reject (R)", command=self.do_reject)
        self.rejectButton.pack(side=LEFT)
        self.undoButton = ttk.Button(self.topBar, text="Undo (U)", command=self.do_undo)
        self.undoButton.pack(side=LEFT)
        self.markAsIsButton = ttk.Button(self.topBar, text="Mark As-Is", command=self.do_mark_as_is)
        self.markAsIsButton.pack(side=RIGHT)

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
        self.tree.bind("<Key>", self.on_tree_key)
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

    def on_destroy(self, ev):
        """called when my top-level window is closed
        this is the easiest and most common way to destroy Medit,
        and includes the case where the entire shoebox application is shut down
        """
        self.top = None
        self.destroy()

    def destroy(self):
        """destroy and clean up this Medit
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
        """Medit destructor"""
        self.destroy() #probably already called
        LogHelper.__del__(self)

    def set_status(self, msg, error=False):
        """set status to specified string"""
        self.statusLabel.configure(text=msg, style="Error.TLabel" if error else "TLabel")
        self.top.update_idletasks()

    def set_status_default(self):
        """set status to default message"""
        if not self.loaded:
            self.set_status("Load a journal file")
        elif self.pxInstNum is not None:
            self.set_status("Using Px {:d}, {:d} meta changes". format(self.pxInstNum, len(self.treeItems)))
        else:
            self.set_status("Ready ({:d} meta changes)".format(len(self.treeItems)))

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

    def update_buttons(self):
        """enable/disable buttons"""
        anySel = len(self.get_selected_items())
        self.enable_widget(self.loadButton, not self.loaded)
        self.enable_widget(self.applyButton, self.loaded and anySel)
        self.enable_widget(self.rejectButton, self.loaded and anySel)
        self.enable_widget(self.undoButton, self.loaded and anySel)
        self.enable_widget(self.markAsIsButton, self.loaded and anySel)

    def do_log(self):
        """when Log button clicked"""
        self.open_log_window("Log - {}".format(self.myName))

    def do_load(self):
        """when load button is clicked"""
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
                self.log_error("Error reading {}: {}".format(self.journalFile, str(e)))
        self.set_status_default_or_error()
        self.update_buttons()

    def clear_tree(self):
        """clear all tree entries"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.treeItems = {}
        self.loaded = False

    def populate_tree(self, metaChgs):
        """populate tree"""
        for mc in metaChgs:
            iid = self.tree.insert('', 'end',
                                   text=mc.id,
                                   values=(mc.prop,
                                           self.annotate_value(mc.prop, mc.val),
                                           self.annotate_value(mc.prop, mc.oldval),
                                           mc.formattedTs, mc.userId, mc.status))
            self.treeItems[iid] = mc
            mc.iid = iid

    def annotate_value(self, prop, val):
        """annotate value"""
        if prop == 'rating':
            try:
                return pic.ratings[val]
            except:
                return val
        else:
            return val

    def update_status_all(self):
        """update status for all meta changes"""
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

    def update_tree_all(self):
        """update all tree items"""
        for iid in self.treeItems:
            self.update_tree_item(iid)

    def update_tree_item(self, iid):
        """update tree item"""
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
        self.tree.set(iid, 'was', self.annotate_value(mc.prop, mc.oldval))
        self.tree.item(iid, tags=tags)

    def on_tree_select(self, event):
        """when user clicks tree item"""
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
                items = [self.treeItems[iid] for iid in sel]
                folderId = pic.get_folder_id(items[0].parts)
                pxInst.goto([item.id for item in items if pic.get_folder_id(item.parts) == folderId])
            else:
                self.set_status("No Px found, please create one")
                self.pxInstNum = None

    def deselect_shadowed_items(self):
        """clear shadowed items from selection"""
        for iid in self.tree.selection():
            if self.treeItems[iid].shadowed:
                self.tree.selection_remove(iid)

    def get_selected_items(self):
        """get selected items"""
        sel = self.tree.selection()
        if len(sel):
            return [self.treeItems[iid] for iid in sel]
        else:
            return [mc for mc in self.mcOrder if mc.softSelected]

    def soft_deselect_all(self):
        """clear soft selections"""
        for iid, mc in self.treeItems.items():
            if mc.softSelected:
                mc.softSelected = False
                self.update_tree_item(iid)

    def do_apply(self):
        """when apply clicked"""
        ids = []
        for mc in self.get_selected_items():
            self.tree.selection_remove(mc.iid)
            mc.softSelected = True
            if mc.apply(self.env):
                ids.append(mc.id)
        self.update_status_all()
        self.update_tree_all()
        self.set_status("{} items applied".format(len(ids)))
        self.update_buttons()
        self.update_px_from_meta(ids)
        metacache.write_all_changes(self.env)

    def do_reject(self):
        """when reject clicked"""
        ids = []
        for mc in self.get_selected_items():
            self.tree.selection_remove(mc.iid)
            mc.softSelected = True
            if mc.reject(self.env):
                ids.append(mc.id)
        self.update_status_all()
        self.update_tree_all()
        self.set_status("{} items rejected".format(len(ids)))
        self.update_buttons()
        self.update_px_from_meta(ids)
        metacache.write_all_changes(self.env)

    def do_undo(self):
        """when undo clicked"""
        ids = []
        for mc in self.get_selected_items():
            self.tree.selection_remove(mc.iid)
            mc.softSelected = True
            if mc.undo(self.env):
                ids.append(mc.id)
        self.update_status_all()
        self.update_tree_all()
        self.set_status("{} items undone".format(len(ids)))
        self.update_buttons()
        self.update_px_from_meta(ids)
        metacache.write_all_changes(self.env)

    def do_mark_as_is(self):
        """when mark as-is clicked
        change status to applied or rejected based on current value of item
        """
        ids = []
        for mc in self.get_selected_items():
            self.tree.selection_remove(mc.iid)
            mc.softSelected = True
            if mc.mark_as_is(self.env):
                ids.append(mc.id)
                if mc.rejected:
                    # when item is marked as rejected, it may unshadow a prior item
                    # repeat for that item, working backward thru shadowed items
                    i = self.mcOrder.index(mc)
                    while self.mcOrder[i].rejected and i > 0 and self.mcOrder[i-1].shadowed:
                        self.mcOrder[i-1].mark_as_is(self.env)
                        i -= 1
        self.update_status_all()
        self.update_tree_all()
        self.set_status("{} items marked as-is".format(len(ids)))
        self.update_buttons()
        # no need to update px or write metacache because nothing really changed

    def update_px_from_meta(self, ids):
        """update px instance from metadata"""
        pxInst = px.get_instance(self.pxInstNum)
        if pxInst:
            pxInst.update_from_meta(ids)

    def on_tree_key(self, event):
        """handle keyboard events for tree"""
        if (event.keycode == ord('A')):
            self.do_apply()
        elif (event.keycode == ord('R')):
            self.do_reject()
        elif (event.keycode == ord('U')):
            self.do_undo()
