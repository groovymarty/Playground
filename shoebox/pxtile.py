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
        self.parts = None
        self.id = None
        self.noncanon = True
        self.errors = 0
        self.selected = False
        self.h0 = 0 #height of item[0]
        self.h = 0 #total height of tile
        self.text = name

    def set_error(self, errBit):
        self.errors |= errBit

    def is_error(self, errBit):
        return self.errors & errBit

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

    def pick_text_color(self):
        return "orange" if self.errors else "cyan" if self.noncanon else "white"

    def set_text(self, text):
        self.text = text

    def redraw_text(self, canvas, w):
        hOld = self.h
        if len(self.items) >= 2:
            # get coordinates of tile
            x, y = canvas.coords(self.items[0])
            # delete old text
            canvas.delete(self.items[1])
            # create new text
            txt = canvas.create_text(x, y + self.h0, text=self.text, anchor=NW, width=w, fill=self.pick_text_color())
            # update tile height
            bb = canvas.bbox(txt)
            self.h = self.h0 + bb[3] - bb[1]
            # update items tuple
            self.items = (self.items[0], txt) + self.items[2:]
        # return change in height
        return self.h - hOld

class PxTilePic(PxTile):
    def __init__(self, name, photo, env=None):
        super().__init__(name, env)
        self.photo = photo
        self.parts = pic.parse_file(self.name, env)
        self.id = self.parts.id if self.parts else None
        # noncanonical means ID can't be parsed from name
        self.noncanon = not self.id

    def add_to_canvas(self, canvas, x, y, w):
        img = canvas.create_image(x, y, image=self.photo, anchor=NW)
        self.h0 = self.photo.height()
        txt = canvas.create_text(x, y + self.h0, text=self.text, anchor=NW, width=w, fill=self.pick_text_color())
        bb = canvas.bbox(txt)
        self.h = self.h0 + bb[3] - bb[1]
        self.items = (img, txt)

class PxTileFile(PxTile):
    def __init__(self, name, env=None):
        super().__init__(name, env)
        self.noncanon = True #always noncanonical

    def add_to_canvas(self, canvas, x, y, w):
        rect = canvas.create_rectangle(x, y, x+fileBoxSz, y+fileBoxSz, fill="gray")
        line = canvas.create_line(x, y, x+fileBoxSz, y+fileBoxSz)
        self.h0 = fileBoxSz
        txt = canvas.create_text(x, y + self.h0, text=self.name, anchor=NW, width=w, fill=self.pick_text_color())
        bb = canvas.bbox(txt)
        self.h = self.h0 + bb[3] - bb[1]
        self.items = (rect, txt, line)
