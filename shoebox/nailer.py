# shoebox.nailer

import os, io
from tkinter import *
from tkinter import ttk, filedialog
from tkit.widgetgarden import WidgetGarden
from shoebox import pic, nails, nailcache
from PIL import Image
from datetime import datetime

instances = []
nextInstNum = 1
delayMs = 15

def printdelta(tstart, what):
    tnow = datetime.now()
    delta = tnow - tstart
    if (delta.seconds or delta.microseconds > 10000):
        print("{:02d}.{:06d} {}".format(delta.seconds, delta.microseconds, what))
    return tnow

class Nailer:
    def __init__(self, path):
        global nextInstNum
        self.instNum = nextInstNum
        nextInstNum += 1
        self.top = Toplevel()
        self.top.geometry("800x180")
        self.top.title("Nailer {:d}".format(self.instNum))
        self.top.bind('<Destroy>', self.on_destroy)
        instances.append(self)

        self.garden = WidgetGarden()
        self.garden.labelText = {'path': "Starting Path:", 'recursive': "Recursive", 'fast': "Fast"}
        self.garden.begin_layout(self.top, 3)
        self.top.grid_columnconfigure(1, weight=1)
        self.garden.make_entry('path')
        self.pathButton = ttk.Button(self.garden.curParent, text="Browse", command=self.do_browse_path)
        self.garden.grid_widget(self.pathButton)
        self.garden.next_row()
        self.garden.next_col()
        self.garden.make_checkbutton('recursive')
        self.garden.next_row()
        self.garden.next_col()
        self.garden.make_checkbutton('fast')
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
        self.garden.next_col()
        self.stopButton = ttk.Button(self.garden.curParent, text="Stop", command=self.do_stop)
        self.garden.grid_widget(self.stopButton)
        self.garden.disable_widget(self.stopButton)
        self.garden.end_layout()

        self.absPath = os.path.abspath(path)
        self.garden.write_var('path', self.absPath)
        self.recursive = True
        self.garden.write_var('recursive', self.recursive)
        self.fast = False
        self.garden.write_var('fast', self.fast)
        self.foldersToScan = None
        self.curScan = None
        self.curEnt = None
        self.curSzIndx = 0
        self.curImage = None
        self.curFolder = ""
        self.quit = False
        self.bufs = []
        self.nFolders = 0
        self.nPictures = 0
        self.tstart = None

    # called when my top-level window is closed
    # this is the easiest and most common way to destroy Nailer,
    # and includes the case where the entire shoebox application is shut down
    def on_destroy(self, ev):
        self.top = None
        self.destroy()

    # destroy and clean up this Nailer
    # in Python you don't really destroy objects, you just remove all references to them
    # so this function removes all known references then closes the top level window
    # note this will result in a second call from the on_destroy event handler; that's ok
    def destroy(self):
        if self in instances:
            instances.remove(self)
        if self.top is not None:
            self.top.destroy()
            self.top = None

    # Nailer destructor
    def __del__(self):
        self.destroy() #probably already called

    # when browse button is clicked
    def do_browse_path(self):
        newDir = filedialog.askdirectory(title="Nailer {} - Select Starting Path".format(self.instNum),
                                         initialdir=self.absPath)
        if newDir:
            self.absPath = newDir
            self.garden.write_var('path', self.absPath)

    # return delay in milliseconds
    def get_delay_ms(self):
        return 0 if self.fast else delayMs

    # when start button is clicked
    def do_start(self):
        self.disable_widgets()
        self.absPath = self.garden.read_var('path')
        self.recursive = self.garden.read_var('recursive')
        self.fast = self.garden.read_var('fast')
        self.foldersToScan = [self.absPath]
        self.curFolder = None
        self.curScan = None
        self.curEnt = None
        self.curSzIndx = 0
        self.curImage = None
        self.quit = False
        self.nFolders = 0
        self.nPictures = 0
        self.update_totals()
        self.tstart = datetime.now()
        self.top.after(self.get_delay_ms(), self.do_next)

    # when stop button clicked
    def do_stop(self):
        self.quit = True

    # do the next thing to do
    def do_next(self):
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
                    self.curFolderLabel.configure(text=self.curFolder)
                    self.nFolders += 1
                    self.update_totals()
                    self.curScan = os.scandir(self.curFolder)
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
                       self.foldersToScan.append(ent.path)
                elif os.path.splitext(ent.path)[1].lower() in pic.pictureExts:
                    # is a picture, set up size iteration
                    self.curPictureLabel.configure(text=ent.name)
                    self.nPictures += 1
                    self.update_totals()
                    self.curEnt = ent
                    self.curSzIndx = 0
                    self.curImage = None
                    break
        # that's all for now, come back soon
        self.top.after(self.get_delay_ms(), self.do_next)

    # update totals
    def update_totals(self):
        self.totalLabel.configure(text="{:d} folders, {:d} pictures".format(self.nFolders, self.nPictures))

    # begin processing a folder
    def begin_folder(self):
        # bufs is array of (index dictionary, byte array of concatenated PNG files) for each thumbnail size
        # index key is picture file name
        # index value is (offset, length) of PNG file in byte array
        self.bufs = [({}, bytearray()) for sz in pic.nailSizes]
        pass

    # process one picture, one size
    def do_picture(self):
        #tstart = datetime.now()
        (indx, buf) = self.bufs[self.curSzIndx]
        sz = pic.nailSizes[self.curSzIndx]

        # first check loose file cache
        imCopy = nailcache.get_loose_file(self.curEnt.path, sz)
        if not imCopy:
            # open and read picture file (this is expensive because pic files are a couple GB or larger)
            if self.curImage is None:
                im = Image.open(self.curEnt.path)
                #tstart = printdelta(tstart, "open and read")

                # thumbnails don't contain EXIF information so correct the image orientation now
                self.curImage = pic.fix_image_orientation(im)
                #tstart = printdelta(tstart, "fix orientation")

            # make a copy (except last time) because thumbnail() modifies the image
            if self.curSzIndx < len(pic.nailSizes)-1:
                imCopy = self.curImage.copy()
                #tstart = printdelta(tstart, "make copy")
            else:
                imCopy = self.curImage

            # make thumbnail of desired size
            imCopy.thumbnail((sz, sz))
            #tstart = printdelta(tstart, "make thumbnail")

        # write to PNG file in memory
        f = io.BytesIO()
        imCopy.save(f, "png")
        #tstart = printdelta(tstart, "save to mem io")

        # append to byte array and compute offset, length
        offset = len(buf)
        buf.extend(f.getvalue())
        #tstart = printdelta(tstart, "copy to buf")

        length = len(buf) - offset
        f.close()
        # add to index
        indx[self.curEnt.name] = (offset, length)

    # finish processing a folder
    def finish_folder(self):
        for i, (indx, buf) in enumerate(self.bufs):
            # don't write empty files
            if len(buf):
                nails.write_nails(self.curFolder, pic.nailSizes[i], indx, buf)

    # when nothing more to do (or quitting because stop button clicked)
    def do_end(self):
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

    # disable most widgets during scan (or enable them afterward)
    def disable_widgets(self, disable=True):
        self.garden.set_widget_disable('path', disable)
        self.garden.set_widget_disable('recursive', disable)
        self.garden.disable_widget(self.pathButton, disable)
        self.garden.disable_widget(self.startButton, disable)
        self.garden.disable_widget(self.stopButton, not disable)
