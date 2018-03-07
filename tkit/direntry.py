# tkit.direntry

import os

# similar to objects returned by dirscan()
class DirEntry:
    def __init__(self, path, isDir=False):
        self.path = path
        self.name = os.path.split(path)[1]
        self.isDir = isDir

    def is_file(self):
        return not self.isDir

    def is_dir(self):
        return self.is_dir

class DirEntryFile(DirEntry):
    def __init__(self, path):
        super().__init__(path, False)

class DirEntryDir(DirEntry):
    def __init__(self, path):
        super().__init__(path, True)
