# shoebox.dnd

targets = {}

def add_target(w, target, name):
    targets[w] = (target, name)

def remove_target(w):
    if w in targets:
        del targets[w]

def get_target_name(w):
    return targets[w][1] if w in targets else ""

def try_drop(w, items):
    if w in targets:
        target, name = targets[w]
        # return True to accept all items
        # return False to reject all items
        # or return array of True/False to accept items individually
        # if array is shorter than items, remaining items are rejected
        return target.receive_drop(items)
    else:
        return False

# item kinds
ID=1    #groovy ID
ENT=2   #scandir entry or equivalent

class DndItem:
    def __init__(self, kind, thing):
        self.kind = kind
        self.thing = thing

class DndItemEnt(DndItem):
    def __init__(self, ent):
        super().__init__(ENT, ent)

class DndItemId(DndItem):
    def __init__(self, id):
        super().__init__(ID, id)
