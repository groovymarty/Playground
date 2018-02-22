# shoebox.pxfolder

from shoebox import pic

class PxFolder:
    def __init__(self, parent, name, path, iid):
        self.parent = parent
        self.name = name
        self.path = path
        self.iid = iid
        self.children = []
        parts = pic.parse_folder(self.name)
        self.id = parts.id if parts else None
        # this folder is noncanonical if ID can't be parsed from name,
        # or if it lies in a subtree under a noncanonical parent
        # root folder (no parent) must be noncanon=false or all folders would be noncanonical!
        self.noncanon = parent and (parent.noncanon or not self.id)

    def add_child(self, folder):
        self.children.append(folder)
