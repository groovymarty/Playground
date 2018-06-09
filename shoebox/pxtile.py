# shoebox.pxtile

from tkinter import *
from tkinter import ttk, font
from shoebox import pic

fileBoxSz = 128

selectColors = {
    1:  "yellow",
    2:  "lime",
    3:  "red",
    4:  "cyan",
    5:  "fuchsia",
    6:  "dodgerblue"
}

fontSymbol = None
fontWingdings2 = None
ratingIcons = []

def make_fonts():
    global fontSymbol, fontWingdings2, ratingIcons
    fontSymbol = font.Font(family="Symbol")
    fontWingdings2 = font.Font(family="Wingdings 2")
    ratingIcons = [
        (fontWingdings2, chr(42),  -3, "gray"),        # 0: empty box
        (fontWingdings2, chr(210),  0, "fuchsia"),     # 1: X
        (fontSymbol,     chr(187), -4, "white"),       # 2: wavy lines
        (fontWingdings2, chr(80),   0, "lime"),        # 3: check
        (fontWingdings2, chr(234),  0, "deepskyblue"), # 4: star
        (fontSymbol,     chr(169), -3, "red"),         # 5: heart
    ]

def make_rating_icon(canvas, x, y, rating):
    try:
        fnt, ch, dy, color = ratingIcons[rating]
    except IndexError:
        if fontSymbol is None:
            make_fonts()
            return make_rating_icon(canvas, x, y, rating)
        fnt, ch, dy, color = ratingIcons[0]
    return canvas.create_text(x, y + dy, text=ch, font=fnt, fill=color, anchor=NW)

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

    def set_name(self, name, env=None):
        self.text = self.name = name

    def set_error(self, errBit):
        self.errors |= errBit

    def clear_error(self, errBit):
        self.errors &= ~errBit

    def is_error(self, errBit):
        return self.errors & errBit

    def is_numbered(self):
        """return true if tile is numbered and has no errors besides OOO"""
        return self.id and not (self.errors & ~pic.OOO)

    def draw_selected(self, canvas, color):
        """note this method cannot be used to change the selection color, must erase_selection first"""
        if not self.selected:
            self.selected = color
            bb = canvas.bbox(self.items[0])
            # this makes a 3px yellow border plus 1px gap around image and text
            r = canvas.create_rectangle(bb[0]-3, bb[1]-3, bb[2]+2, bb[1]+self.h+2,
                                        outline=selectColors[color], width=3)
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

    def redraw_text(self, canvas, w):
        hOld = self.h
        if len(self.items) >= 2:
            # get coordinates of tile
            x, y = canvas.coords(self.items[0])[:2]
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

    def erase(self, canvas):
        for item in self.items:
            canvas.delete(item)
        self.selected = False

    def move(self, canvas, dx, dy):
        for item in self.items:
            canvas.move(item, dx, dy)

class PxTilePic(PxTile):
    def __init__(self, name, photo, metaDict=None, env=None):
        super().__init__(name, env)
        self.photo = photo
        self.parse_name(env)
        self.caption = None
        self.rating = 0
        if self.id and metaDict:
            metaDict.restore_meta_from_loose_cache(self.id, name)
            self.set_caption(metaDict.get_caption(self.id))
            self.set_rating(metaDict.get_rating(self.id))
        else:
            self.make_text()

    def set_name(self, name, env=None):
        self.name = name
        self.parse_name(env)
        self.make_text()

    def parse_name(self, env):
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
        icon = make_rating_icon(canvas, x, y + self.h0, self.rating)
        self.items = (img, txt, icon)

    def set_caption(self, caption):
        self.caption = caption
        self.make_text()

    def set_rating(self, rating):
        self.rating = rating

    def make_text(self):
        # leave space at the beginning for the icon
        lines = ["     {}".format(self.name)]
        if self.caption:
            lines.append(self.caption)
        self.text = "\n".join(lines)

    def redraw_icon(self, canvas):
        if len(self.items) >= 3:
            # get coordinates of tile
            x, y = canvas.coords(self.items[0])[:2]
            # delete old icon
            canvas.delete(self.items[2])
            # create new icon
            icon = make_rating_icon(canvas, x, y + self.h0, self.rating)
            # update items tuple
            self.items = (self.items[0], self.items[1], icon) + self.items[3:]

class PxTileFile(PxTile):
    def __init__(self, name, env=None):
        super().__init__(name, env)

    def add_to_canvas(self, canvas, x, y, w):
        rect = canvas.create_rectangle(x, y, x+fileBoxSz, y+fileBoxSz, fill="gray")
        line = canvas.create_line(x, y, x+fileBoxSz, y+fileBoxSz)
        self.h0 = fileBoxSz
        txt = canvas.create_text(x, y + self.h0, text=self.text, anchor=NW, width=w, fill=self.pick_text_color())
        bb = canvas.bbox(txt)
        self.h = self.h0 + bb[3] - bb[1]
        self.items = (rect, txt, line)

class PxTileContent(PxTile):
    def __init__(self, name, env=None):
        super().__init__(name, env)

    def add_to_canvas(self, canvas, x, y, w):
        rect = canvas.create_rectangle(x, y, x+fileBoxSz, y+fileBoxSz, fill="gray")
        # disable circle so mouse click event will occur in rect
        line = canvas.create_oval(x+20, y+20, x+fileBoxSz-20, y+fileBoxSz-20, fill="orange", state=DISABLED)
        self.h0 = fileBoxSz
        txt = canvas.create_text(x, y + self.h0, text=self.text, anchor=NW, width=w, fill=self.pick_text_color())
        bb = canvas.bbox(txt)
        self.h = self.h0 + bb[3] - bb[1]
        self.items = (rect, txt, line)

class PxTileHole(PxTile):
    def __init__(self, env=None):
        super().__init__("(hole)", env)

    def add_to_canvas(self, canvas, bbox):
        # if only start coordinates given, use file box size
        if len(bbox) == 2:
            bbox += bbox[0] + fileBoxSz, bbox[1] + fileBoxSz
        rect = canvas.create_rectangle(*bbox, fill="black", outline="gray", width=1, dash=[2,2])
        self.h0 = bbox[3] - bbox[1]
        self.h = self.h0
        self.items = [rect]
