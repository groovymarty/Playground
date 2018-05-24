# shoebox.nailer

import os, io
from tkinter import *
from tkinter import ttk, filedialog
from tkit.widgetgarden import WidgetGarden
from tkit.direntry import DirEntry
from shoebox import pic, nails, nailcache
from PIL import Image
from datetime import datetime
from tkit.loghelper import LogHelper
from pathlib import Path

instances = []
nextInstNum = 1
delayMs = 15

def printdelta(tstart, what):
    tnow = datetime.now()
    delta = tnow - tstart
    if (delta.seconds or delta.microseconds > 10000):
        print("{:02d}.{:06d} {}".format(delta.seconds, delta.microseconds, what))
    return tnow

class Folder:
    def __init__(self, ent, parent):
        self.ent = ent
        self.parent = parent

class Nailer(LogHelper):
    def __init__(self, path):
        self.env = {}
        LogHelper.__init__(self, self.env)
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1
        self.top = Toplevel()
        self.top.geometry("800x250")
        self.top.title("Nailer {:d}".format(self.instNum))
        self.top.bind('<Destroy>', self.on_destroy)
        instances.append(self)

        self.garden = WidgetGarden()
        self.garden.labelText = {
            'path': "Starting Path:",
            'recursive': "Recursive",
            'quick': "Quick, create missing nail files only",
            'force': "Force, make all new thumbnails"}
        self.garden.begin_layout(self.top, 3)
        self.top.grid_columnconfigure(1, weight=1)
        self.garden.make_entry('path')
        self.pathButton = ttk.Button(self.garden.curParent, text="Browse", command=self.do_browse_path)
        self.garden.grid_widget(self.pathButton)
        self.garden.next_row()
        self.garden.next_col()
        self.garden.make_checkbutton('recursive')
        self.logButton = ttk.Button(self.garden.curParent, text="Log", command=self.do_log)
        self.garden.grid_widget(self.logButton)
        self.garden.next_row()
        self.garden.next_col()
        self.garden.make_checkbutton('quick')
        self.garden.next_row()
        self.garden.next_col()
        self.garden.make_checkbutton('force')
        self.garden.next_row()
        self.garden.next_col()
        self.startButton = ttk.Button(self.garden.curParent, text="Start", command=self.do_start)
        self.garden.grid_widget(self.startButton)
        self.garden.next_row()
        self.garden.grid_widget(ttk.Label(self.garden.curParent, text="Doing folder:"))
        self.garden.next_col()
        self.curFolderLabel = ttk.Label(self.garden.curParent)
        self.garden.grid_widget(self.curFolderLabel)
        self.garden.next_row()
        self.garden.grid_widget(ttk.Label(self.garden.curParent, text="Doing picture:"))
        self.garden.next_col()
        self.curPictureLabel = ttk.Label(self.garden.curParent)
        self.garden.grid_widget(self.curPictureLabel)
        self.garden.next_row()
        self.garden.grid_widget(ttk.Label(self.garden.curParent, text="Total:"))
        self.garden.next_col()
        self.totalLabel = ttk.Label(self.garden.curParent)
        self.garden.grid_widget(self.totalLabel)
        self.garden.next_row()
        self.garden.grid_widget(ttk.Label(self.garden.curParent, text="Nails made:"))
        self.garden.next_col()
        self.madeLabel = ttk.Label(self.garden.curParent)
        self.garden.grid_widget(self.madeLabel)
        self.garden.next_row()
        self.garden.grid_widget(ttk.Label(self.garden.curParent, text="Cache:"))
        self.garden.next_col()
        self.cacheLabel = ttk.Label(self.garden.curParent)
        self.garden.grid_widget(self.cacheLabel)
        self.garden.next_row()
        self.garden.next_col()
        self.stopButton = ttk.Button(self.garden.curParent, text="Stop", command=self.do_stop)
        self.garden.grid_widget(self.stopButton)
        self.garden.disable_widget(self.stopButton)
        self.garden.end_layout()

        self.absPath = os.path.abspath(path)
        self.garden.write_var('path', self.absPath)
        self.recursive = True
        self.garden.write_var('recursive', self.recursive)
        self.quick = False
        self.garden.write_var('quick', self.quick)
        self.force = False
        self.garden.write_var('force', self.force)
        self.foldersToScan = None
        self.curFolder = None
        self.curScan = None
        self.skipping = False
        self.curEnt = None
        self.curSzIndx = 0
        self.curImage = None
        self.quit = False
        self.bufs = []
        self.nFolders = 0
        self.nPictures = 0
        self.nNailImagesMade = 0
        self.nNailFilesMade = 0
        self.tstart = None
        self.update_cache_status()

    def on_destroy(self, ev):
        """called when my top-level window is closed
        this is the easiest and most common way to destroy Nailer,
        and includes the case where the entire shoebox application is shut down"""
        self.top = None
        self.destroy()

    def destroy(self):
        """destroy and clean up this Nailer
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
        """Nailer destructor"""
        self.destroy() #probably already called

    def do_browse_path(self):
        """when browse button is clicked"""
        newDir = filedialog.askdirectory(title="Nailer {} - Select Starting Path".format(self.instNum),
                                         initialdir=self.absPath)
        if newDir:
            self.absPath = newDir
            self.garden.write_var('path', self.absPath)

    def do_log(self):
        """when Log button clicked"""
        self.open_log_window("Log - Nailer {:d}".format(self.instNum))

    def get_delay_ms(self):
        """return delay in milliseconds"""
        return delayMs

    def do_start(self):
        """when start button is clicked"""
        self.disable_widgets()
        self.absPath = self.garden.read_var('path')
        self.recursive = self.garden.read_var('recursive')
        self.quick = self.garden.read_var('quick')
        self.force = self.garden.read_var('force')
        self.foldersToScan = [Folder(DirEntry(self.absPath), None)]
        self.curFolder = None
        self.curScan = None
        self.skipping = False
        self.curEnt = None
        self.curSzIndx = 0
        self.curImage = None
        self.quit = False
        self.nFolders = 0
        self.nPictures = 0
        self.nNailFilesMade = 0
        self.nNailImagesMade = 0
        self.update_totals()
        self.tstart = datetime.now()
        self.top.after(self.get_delay_ms(), self.do_next)

    def do_stop(self):
        """when stop button clicked"""
        self.quit = True

    def do_next(self):
        """do the next thing to do"""
        # possibly quit
        if self.quit:
            self.do_end()
            return
        # possibly do next size for current picture
        if self.curEnt and self.curSzIndx < len(pic.nailSizes):
            self.do_picture()
            self.curSzIndx += 1
        else:
            # possibly advance to next folder
            if self.curScan is None:
                if len(self.foldersToScan):
                    self.curFolder = self.foldersToScan.pop()
                    self.curFolderLabel.configure(text=self.curFolder.ent.path)
                    self.curPictureLabel.configure(text="")
                    self.nFolders += 1
                    self.update_totals()
                    self.curScan = os.scandir(self.curFolder.ent.path)
                    self.curEnt = None
                    self.begin_folder()
                else:
                    self.do_end()
                    return
            # loop until we find next picture or end of scan
            while self.curScan:
                ent = next(self.curScan, None)
                if ent is None:
                    # scan is done
                    self.curScan = None
                    self.curEnt = None
                    self.finish_folder()
                    break
                elif ent.is_dir():
                    # is a directory, remember for later if recursive
                    if self.recursive:
                        self.foldersToScan.append(Folder(ent, self.curFolder))
                elif os.path.splitext(ent.path)[1].lower() in pic.pictureExts:
                    # is a picture, set up size iteration
                    self.nPictures += 1
                    self.update_totals()
                    if not self.skipping:
                        self.curPictureLabel.configure(text=ent.name)
                        self.curEnt = ent
                        self.curSzIndx = 0
                        self.curImage = None
                        break
        # that's all for now, come back soon
        self.top.after(self.get_delay_ms(), self.do_next)

    def update_totals(self):
        """update totals"""
        self.totalLabel.configure(text="{:d} folders, {:d} pictures".format(self.nFolders, self.nPictures))
        self.madeLabel.configure(text="{:d} files, {:d} images".format(self.nNailFilesMade, self.nNailImagesMade))
        self.update_cache_status()

    def begin_folder(self):
        """begin processing a folder"""
        self.skipping = self.quick and self.all_nails_exist(self.curFolder.ent.path)
        if not self.skipping:
            # bufs is array of (index dictionary, byte array of concatenated PNG files) for each thumbnail size
            # index key is picture file name
            # index value is (offset, length) of PNG file in byte array
            self.bufs = [({}, bytearray()) for sz in pic.nailSizes]
            if not self.force:
                # preload all sizes
                for sz in pic.nailSizes:
                    try:
                        nailcache.get_nails(self.curFolder.ent.path, sz, self.env)
                    except:
                        pass
                # explode any nails files we have in cache for this folder to the loose file cache
                nailcache.explode_nails(self.curFolder.ent.path)
                self.update_cache_status()

    def do_picture(self):
        """process one picture, one size"""
        (indx, buf) = self.bufs[self.curSzIndx]
        sz = pic.nailSizes[self.curSzIndx]

        # first check loose file cache
        imCopy = None
        if not self.force:
            # note this could be image or PNG data, assume image for now
            imCopy = nailcache.get_loose_file(self.curEnt.path, sz)

        # clear loose file from cache in any case
        nailcache.clear_loose_file(self.curEnt.path, sz)

        # if still no image, make new thumbnail
        if not imCopy:
            # open and read picture file (this is expensive because pic files are a couple GB or larger)
            if self.curImage is None:
                im = Image.open(self.curEnt.path)

                # thumbnails don't contain EXIF information so correct the image orientation now
                self.curImage = pic.fix_image_orientation(im)

            # make a copy (except last time) because thumbnail() modifies the image
            if self.curSzIndx < len(pic.nailSizes)-1:
                imCopy = self.curImage.copy()
            else:
                imCopy = self.curImage

            # make thumbnail of desired size
            imCopy.thumbnail((sz, sz))
            self.nNailImagesMade += 1
            self.update_totals()

        offset = len(buf)
        if pic.is_pil_image(imCopy):
            # write to PNG file in memory
            f = io.BytesIO()
            imCopy.save(f, "png")

            # append to byte array
            buf.extend(f.getvalue())
            f.close()
        else:
            # it was PNG data, no need to make image
            buf.extend(imCopy)

        length = len(buf) - offset
        # add to index
        indx[self.curEnt.name] = (offset, length)

    def finish_folder(self):
        """finish processing a folder"""
        if not self.skipping:
            for i, (indx, buf) in enumerate(self.bufs):
                # don't write empty files
                if len(buf):
                    nails.write_nails(self.curFolder.ent.path, pic.nailSizes[i], indx, buf)
                    self.nNailFilesMade += 1
                    self.update_totals()
                    # clear any leftover files from cache
                    nailcache.clear_nails(self.curFolder.ent.path, self.env)
                    self.update_cache_status()

    def do_end(self):
        """when nothing more to do (or quitting because stop button clicked)"""
        self.curScan = None
        self.curImage = None
        self.foldersToScan = None
        delta = datetime.now() - self.tstart
        msg = "{} {:d}.{:d} sec".format(
            "Stopped" if self.quit else "Complete",
            delta.seconds,
            round(delta.microseconds/1000))
        self.curFolderLabel.configure(text=msg)
        self.curPictureLabel.configure(text="")
        self.disable_widgets(False)

    def disable_widgets(self, disable=True):
        """disable most widgets during scan (or enable them afterward)"""
        self.garden.set_widget_disable('path', disable)
        self.garden.set_widget_disable('recursive', disable)
        self.garden.set_widget_disable('quick', disable)
        self.garden.set_widget_disable('force', disable)
        self.garden.disable_widget(self.pathButton, disable)
        self.garden.disable_widget(self.startButton, disable)
        self.garden.disable_widget(self.stopButton, not disable)

    def update_cache_status(self):
        """update cache status"""
        msg = "{} nails, {} loose files".format(nailcache.cacheCount, nailcache.looseCount)
        self.cacheLabel.configure(text=msg)

    def all_nails_exist(self, folderPath):
        """return true if all nail files exist for specified folder"""
        for sz in pic.nailSizes:
            path = os.path.join(folderPath, nails.build_file_name(sz))
            if not Path(path).exists():
                return False
        return True
