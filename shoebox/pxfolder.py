# shoebox.pxfolder

from shoebox import pic

class PxFolder:
    def __init__(self, parent, name, path, iid, env=None):
        self.parent = parent
        self.name = name
        self.path = path
        self.iid = iid
        self.children = []
        self.parts = pic.parse_folder(self.name, env)
        self.id = self.parts.id if self.parts else None
        # a folder is noncanonical if ID can't be parsed from name,
        # or if it lies in a subtree under a noncanonical parent
        # force root folder (no parent) to be canonical else all folders would be noncanonical!
        self.noncanon = parent and (parent.noncanon or not self.id)
        self.errors = 0

    def add_child(self, folder):
        self.children.append(folder)

    def set_error(self, errBit):
        self.errors |= errBit

    def is_error(self, errBit):
        return self.errors & errBit
