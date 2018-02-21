# shoebox.pic

import re
from collections import namedtuple

pictureExts = [".jpg", ".jpeg", ".gif", ".png", ".tif"]

nailSizes = [128, 244]

# named tuple returned by parse functions
#                            |0        |1       |2      |3       |4     |5     |6     |7         |8     |9      |10
Parts = namedtuple('Parts', ['parent', 'child', 'type', 'zeros', 'num', 'ver', 'sep', 'comment', 'ext', 'what', 'id'])

#                         parentBase    parentSfx  child          sep    comment
#                         |1            |2         |3             |4     |5
folderPat = re.compile(r"^([A-Za-z]+\d*)([A-Za-z]*)(\d*(?:\+\d+)*)([- ]*)(.*)")

#                       parentBase    parentSfx  child           type       z   num       ver        sep    commentExt
#                       |1            |2         |3              |4         |5  |6        |7         |8     |9
filePat = re.compile(r"^([A-Za-z]+\d*)([A-Za-z]*)(\d*(?:\+\d+)*)-([A-Za-z]*)(0*)([1-9]\d*)([A-Za-z]*)([- ]*)(.*)")

# leading plus unnecessary if parent has suffix (and therefore ends with a letter)
def trimChild(mr):
    if mr.group(3).startswith("+") and mr.group(2):
        print("***** Extra plus: "+mr.group())
        return mr.group(3)[1:]
    else:
        return mr.group(3)

def parseFolder(name):
    mr = folderPat.match(name)
    if mr:
        parts = [
            (mr.group(1) + mr.group(2)).upper(), #parent
            trimChild(mr), #child
            None, #type
            None, #zeros
            # child number for sorting or 0 if no child string
            # note rfind returns -1 if not found, plus 1 gives 0 resulting in entire string
            int(mr.group(3)[mr.group(3).rfind("+")+1:] or "0"), #num
            None, #ver
            mr.group(4), #sep
            mr.group(5), #comment
            None, #ext
            "folder"] #what
        if parts[6] or not parts[7]: #has separator or comment is empty
            parts.append("{0}{1}".format(*parts)) #id
            return Parts._make(parts)
    return None

def parseFile(name):
    mr = filePat.match(name)
    if mr:
        # find last dot for extension
        # hard to do in regular expression because extension is optional
        idot = mr.group(9).rfind(".")
        if idot < 0:
            idot = len(mr.group(9))
        parts = [
            (mr.group(1) + mr.group(2)).upper(), #parent
            trimChild(mr), #child
            mr.group(4).upper(), #type
            mr.group(5), #zeros
            int(mr.group(6)), #num
            mr.group(7).upper(), #ver
            mr.group(8), #sep
            mr.group(9)[0:idot], #comment
            mr.group(9)[idot:].lower(), #ext
            "file"] #what
        if parts[6] or not parts[7]: #has separator or comment is empty
            parts.append("{0}{1}-{2}{4:d}{5}".format(*parts)) #id
            return parts
    return None

# return PIL image rotated according to EXIF orientation value
def fix_image_orientation(im):
    if hasattr(im, '_getexif'):
        exif = im._getexif()
        if exif and 274 in exif:  # 274 = Orientation
            orientation = exif[274]
            if orientation == 3:  # 3 = Bottom/Right
                return im.rotate(180, expand=True)
            elif orientation == 6:  # 6 = Right/Top
                return im.rotate(270, expand=True)
            elif orientation == 8:  # 8 = Left/Bottom
                return im.rotate(90, expand=True)
    return im
