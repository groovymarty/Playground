# shoebox.pic

import re, os
from collections import namedtuple
from tkit import environ

pictureExts = [".jpg", ".jpeg", ".gif", ".png", ".tif"]
videoExts = [".mp4", ".mov", ".avi", ".wmv", ".3gp", ".webm"]

nailSizes = [128, 244]
nailSizeNames = ["Small", "Large"]

# error bits
DUP = 0x01  # duplicate
OOP = 0x02  # out of place
OOO = 0x04  # out of order
NF = 0x08   # not found

# max picture number, for sorting
MAXNUM = 999999
MAXSORTNUM = MAXNUM * 729

# comment modes
DISCARD = 0
TRIM2 = 1
KEEPALL = 2

# ratings
ratings = [
    "0 - No Rating",
    "1 - Delete Me",
    "2 - Low Interest",
    "3 - Good",
    "4 - Better",
    "5 - Love it!"
]

def flip_rating(r):
    """flip ratings order for dropdown"""
    if r >= 0 and r < len(ratings):
        return len(ratings) - r - 1
    else:
        return len(ratings) - 1

# named tuple returned by parse functions
Parts = namedtuple('Parts', [
    'parent',   # 0
    'child',    # 1
    'type',     # 2
    'zeros',    # 3
    'num',      # 4
    'ver',      # 5
    'sep',      # 6
    'comment',  # 7
    'ext',      # 8
    'what',     # 9
    'id',       # 10
    'sortNum']) # 11

#                         parentBase    parentSfx  child          sep    comment
#                         |1            |2         |3             |4     |5
folderPat = re.compile(r"^([A-Za-z]+\d*)([A-Za-z]*)(\d*(?:\+\d+)*)([- ]*)(.*)")

#                       parentBase    parentSfx  child           type       z   num       ver            sep  commentExt
#                       |1            |2         |3              |4         |5  |6        |7             |8     |9
filePat = re.compile(r"^([A-Za-z]+\d*)([A-Za-z]*)(\d*(?:\+\d+)*)-([A-Za-z]*)(0*)([1-9]\d*)([A-Za-z]{0,2})([- ]*)(.*)")

#                            type       z   num       ver
#                            |1         |2  |3        |4
secondLumpPat = re.compile(r"([A-Za-z]*)(0*)([1-9]\d*)([A-Za-z]{0,2})")

def trim_child(mr, env):
    """leading plus unnecessary if parent has suffix (and therefore ends with a letter)"""
    if mr.group(3).startswith("+") and mr.group(2):
        environ.log_warning(env, "Extra plus: {}".format(mr.group()))
        return mr.group(3)[1:]
    else:
        return mr.group(3)

def parse_folder(name, env=None):
    mr = folderPat.match(name)
    if mr:
        parts = [
            (mr.group(1) + mr.group(2)).upper(),  # parent
            trim_child(mr, env),  # child
            None,  # type
            None,  # zeros
            # child number for sorting or 0 if no child string
            # note rfind returns -1 if not found, plus 1 gives 0 resulting in entire string
            int(mr.group(3)[mr.group(3).rfind("+") + 1:] or "0"),  # num
            None,  # ver
            mr.group(4),  # sep
            mr.group(5),  # comment
            None,  # ext
            "folder"]  # what
        if parts[6] or not parts[7]:  # has separator or comment is empty
            parts.append("{0}{1}".format(*parts))  # id
            parts.append(parts[4])  # sortNum
            return Parts._make(parts)
    return None

def parse_file(name, env=None):
    mr = filePat.match(name)
    if mr:
        # find last dot for extension
        # hard to do in regular expression because extension is optional
        idot = mr.group(9).rfind(".")
        if idot < 0:
            idot = len(mr.group(9))
        parts = [
            (mr.group(1) + mr.group(2)).upper(),  # parent
            trim_child(mr, env),  # child
            mr.group(4).upper(),  # type
            mr.group(5),  # zeros
            int(mr.group(6)),  # num
            mr.group(7).upper(),  # ver
            mr.group(8),  # sep
            mr.group(9)[0:idot],  # comment
            mr.group(9)[idot:].lower(),  # ext
            "file"]  # what
        if parts[6] or not parts[7]:  # has separator or comment is empty
            parts.append("{0}{1}-{2}{4:d}{5}".format(*parts))  # id
            # make sort number from picture number and version
            # version is up to 2 letters A-Z so 26 letters + 1 for not present = 27
            sortNum = parts[4] * 729  # 27 squared
            if parts[5]:
                sortNum += (ord(parts[5][0]) - ord('A') + 1) * 27
                if len(parts[5]) > 1:
                    sortNum += ord(parts[5][1]) - ord('A') + 1
            parts.append(sortNum)
            return Parts._make(parts)
    return None

def get_folder_id(parts):
    """given parse results, return folder ID"""
    return parts.parent + parts.child

def get_parent_id(parts):
    """given parse results, return ID of parent folder or "" if parent is root"""
    if parts.child:
        if "+" in parts.child:
            return parts.parent + parts.child[0:parts.child.rfind("+")]
        else:
            return parts.parent
    else:
        return ""

def get_num_digits(parts):
    """given parse results for a file, return number of digits in which picture number was written"""
    return len(parts.zeros) + len(str(parts.num))

def parse_noncanon(name, commentMode):
    """parse a noncanonical name, return tuple (junk, version, comment, ext)"""
    basename, ext = os.path.splitext(name)
    if commentMode == TRIM2:
        lumps = basename.split("-")
        ver = ""
        if len(lumps) > 1:
            # parse second lump and extract version
            mr = secondLumpPat.fullmatch(lumps[1])
            if mr:
                # remove version from second lump
                lumps[1] = "".join(mr.group(1,2,3))
                ver = mr.group(4)
        return "-".join(lumps[:2]), ver, "-".join(lumps[2:]), ext
    elif commentMode == KEEPALL:
        return "", "", basename, ext
    else:  # DISCARD
        return basename, "", "", ext

def fix_image_orientation(im):
    """return PIL image rotated according to EXIF orientation value"""
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

def is_pil_image(im):
    """duck test for PIL image, seems they are not all derived from same base class"""
    return hasattr(im, 'thumbnail') and hasattr(im, 'rotate')
