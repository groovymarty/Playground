import os, re, fnmatch, glob
picBaseDir = "\\Users\\Msaus\\Pictures"
num = 890
bump = 10
prefix = "D18A1"
workdir = "_Scratch"

def findPicDir(name):
    match = re.match(r"([A-Z]+\d+[A-Z]+)(\d*).*", name)
    if not match:
        result = os.path.join(picBaseDir, name)
        if not os.path.isdir(result):
            raise Exception("Directory not found: "+name)
    else:
        parentDir = match.group(1)
        dirs = glob.glob(os.path.join(picBaseDir, parentDir+"*"))
        if len(dirs) == 0:
            raise Exception("Directory not found: "+parentDir)
        if len(dirs) > 1:
            raise Exception("More than one directory found: "+parentDir)
        result = dirs[0]
        if match.group(2) != "":
            childDir = match.group(1)+match.group(2)
            # TODO: the following glob matches "D16I1 xx" and "D16I10 yy", which is wrong
            # Space below is temp fix, improve someday..
            dirs = glob.glob(os.path.join(result, childDir+" *"))
            if len(dirs) == 0:
                raise Exception("Child directory not found: "+childDir)
            if len(dirs) > 1:
                raise Exception("More than one child directory found: "+childDir)
            result = dirs[0]
    return result

def getcomment(str):
    return ""
    # Strip off extension
    str = os.path.splitext(str)[0]
    # Strip off IMG_ prefix or similar
    if str.startswith("IMG_"):
        str = str[4:]
    elif str.startswith("imagejpeg_"):
        str = str[10:]
    else:
        # Strip off prefix like D15A- or D15B1-
        match = re.match(r"[ADEF]\d+[A-Z]+\d*-(.*)", str)
        if match:
            str = match.group(1)
    # Strip off leading numbers and punctuation
    match = re.match(r"[-_\d\s]*(.*)", str)
    if match:
        str = match.group(1)
    # Whatever is left is comment string
    # Change spaces to dashes
    str = re.sub(r"[-\s]+", "-", str)
    return str

os.chdir(findPicDir(workdir))

for file in os.listdir("."):
    if fnmatch.fnmatch(file, '*.jpg') or fnmatch.fnmatch(file, '*.jpeg'):
        comment = getcomment(file)
        #temp wedding comment = ""
        #temp wedding match = re.match(r".*-(\d*)", file)
        #temp wedding num = int(match.group(1))
        if bump <= 2:
            newfile = prefix + ("-%03d" % num)
        else:
            newfile = prefix + ("-%04d" % num)
        num += bump
        if comment:
            newfile += "-" + comment
        newfile += ".jpg"
        if file != newfile:
            print(file + " -> " + newfile)
            os.rename(file, newfile)
