# shoebox.pxtile

from tkinter import *
from tkinter import ttk
from shoebox import pic

fileBoxSz = 128

class PxTile:
    def __init__(self, name, env=None):
        self.name = name
        self.items = None
        self.parts = pic.parse_file(self.name, env)
        self.id = self.parts.id if self.parts else None
        # a file is noncanonical if ID can't be parsed from name
        self.noncanon = not self.id
        self.h = 0

class PxTilePic(PxTile):
    def __init__(self, name, photo, env=None):
        super().__init__(name, env)
        self.photo = photo

    def add_to_canvas(self, canvas, x, y, w):
        img = canvas.create_image(x, y, image=self.photo, anchor=NW)
        self.h = self.photo.height()
        txt = canvas.create_text(x, y + self.h, text=self.name, anchor=NW, width=w,
                                 fill="cyan" if self.noncanon else "white")
        bb = canvas.bbox(txt)
        self.h += bb[3] - bb[1]
        self.items = (img, txt)

class PxTileFile(PxTile):
    def __init__(self, name, env=None):
        super().__init__(name, env)

    def add_to_canvas(self, canvas, x, y, w):
        rect = canvas.create_rectangle(x, y, x+fileBoxSz, y+fileBoxSz, fill="gray")
        line = canvas.create_line(x, y, x+fileBoxSz, y+fileBoxSz)
        self.h = fileBoxSz
        txt = canvas.create_text(x, y + self.h, text=self.name, anchor=NW, width=w, fill="cyan")
        bb = canvas.bbox(txt)
        self.h += bb[3] - bb[1]
        self.items = (rect, txt, line)
