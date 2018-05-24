# shoebox.nails

import os
from tkit import environ

def build_file_name(sz):
    """build thumbnail file name for specified size"""
    return "nails-{:d}.xpng".format(sz)

def write_nails(folderPath, sz, indx, pngBytes):
    """index keys are file names, values are (offset, length) of thumbnail for that file in pngBytes
    pngBytes is concatenation of PNG files
    """
    arr = ["{}\t{:d}\t{:d}".format(name, value[0], value[1]) for name, value in indx.items()]
    indexBytes = "\n".join(arr).encode()
    headerBytes = "XPNG0100{:08d}".format(len(indexBytes)).encode()
    if len(headerBytes) != 16:
        raise RuntimeError("Header length is {:d}, expected 16".format(len(headerBytes)))
    path = os.path.join(folderPath, build_file_name(sz))
    with open(path, 'wb') as f:
        f.write(headerBytes)
        f.write(indexBytes)
        f.write(pngBytes)

def read_nails(folderPath, sz):
    """returns (index, pngByes) or raises exception"""
    path = os.path.join(folderPath, build_file_name(sz))
    with open(path, 'rb') as f:
        headerBytes = f.read(16)
        if len(headerBytes) != 16:
            raise RuntimeError("XPNG file too short for header")
        header = headerBytes.decode()
        if header[0:4] != "XPNG":
            raise RuntimeError("Header doesn't look like XPNG file")
        elif header[4:6] != "01":
            raise RuntimeError("Unsupported XPNG file version {}".format(header[4:8]))
        try:
            indexLen = int(header[8:16])
        except ValueError:
            raise RuntimeError("Bad XPNG index length: '{}'".format(header[8:16]))
        indexBytes = f.read(indexLen)
        if len(indexBytes) != indexLen:
            raise RuntimeError("XPNG file too short for index length {:d}".format(indexLen))
        indx = {}
        for indexItem in indexBytes.decode().split("\n"):
            parts = indexItem.split("\t")
            if len(parts) < 3:
                raise RuntimeError("XPNG index item should have 3 fields: '{}'".format(indexItem))
            try:
                offset = int(parts[1])
            except ValueError:
                raise RuntimeError("Bad XPNG offset '{}' for '{}'".format(parts[1], parts[0]))
            try:
                length = int(parts[2])
            except ValueError:
                raise RuntimeError("Bad XPNG length '{}' for '{}'".format(parts[2], parts[0]))
            indx[parts[0]] = (offset, length)
        pngBytes = f.read()
    return (indx, pngBytes)

def delete_nails(folderPath, sz, env=None):
    path = os.path.join(folderPath, build_file_name(sz))
    try:
        os.remove(path)
        environ.log_info(env, "Deleted {}".format(path))
    except FileNotFoundError:
        pass

class Nails:
    def __init__(self, indxAndBytes):
        (self.indx, self.buf) = indxAndBytes
        self.lastTouch = 0

    def has_name(self, name):
        return name in self.indx

    def get_by_name(self, name):
        if name in self.indx:
            (offset, length) = self.indx[name]
            data = self.buf[offset: offset + length]
            if len(data) == length:
                return data
            else:
                raise RuntimeError("Bad XPNG offset={:d}, length={:d} for {}".format(offset, length, name))
        else:
            raise KeyError("No thumbnail for {}".format(name))

    def get_all(self):
        """generates tuples (name, data)"""
        return ((name, self.get_by_name(name)) for name in self.indx)

    def remove(self, name):
        if name in self.indx:
            roffset, rlength = self.indx[name]
            b = bytearray(self.buf[:roffset]) + self.buf[roffset + rlength:]
            self.buf = bytes(b)
            del self.indx[name]
            for name, val in self.indx.items():
                offset, length = val
                if offset > roffset:
                    offset -= rlength
                    self.indx[name] = (offset, length)

    def touch(self, value):
        self.lastTouch = value

    def write(self, folderPath, sz):
        write_nails(folderPath, sz, self.indx, self.buf)
