# shoebox.pxtile

from tkinter import *
from tkinter import ttk
from shoebox import pic

fileBoxSz = 128

class PxTile:
    def __init__(self, name, env=None):
        self.name = name
        # items is tuple with all canvas items for this tile
        # items[0] is main image (or gray box if file tile)
        # items[1] is text
        # additional items follow, such as black slash line in file tile
        # last item is yellow border if selected
        self.items = None
        self.parts = pic.parse_file(self.name, env)
        self.id = self.parts.id if self.parts else None
        # a file is noncanonical if ID can't be parsed from name
        self.noncanon = not self.id
        self.selected = False
        self.h = 0

    def draw_selected(self, canvas):
        if not self.selected:
            self.selected = True
            bb = canvas.bbox(self.items[0])
            # this makes a 3px yellow border plus 1px gap around image and text
            r = canvas.create_rectangle(bb[0]-3, bb[1]-3, bb[2]+2, bb[1]+self.h+2,
                                        outline="yellow", width=3)
            canvas.tag_lower(r)
            self.items += (r,)

    def erase_selected(self, canvas):
        if self.selected:
            self.selected = False
            r = self.items[-1]
            self.items = self.items[0:-1]
            canvas.delete(r)

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
