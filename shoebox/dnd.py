# shoebox.dnd

targets = {}

def add_target(w, target):
    targets[w] = target

def remove_target(w):
    if w in targets:
        del targets[w]

def try_drop(w, items):
    if w in targets:
        return targets[w].receive_drop(items)
    else:
        return False
