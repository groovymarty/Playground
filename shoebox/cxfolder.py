# shoebox.cxfolder

class CxFolder:
    def __init__(self, children, id, name, path):
        self.parent = None  # set later
        self.children = children
        self.id = id
        self.name = name
        self.path = path
        self.iid = None  # set later
