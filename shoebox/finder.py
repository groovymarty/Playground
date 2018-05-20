# shoebox.finder

import os
from shoebox import pic

folders = {"": "."}

def find_folder(id):
    if id in folders:
        return folders[id]
    parts = pic.parse_folder(id)
    if parts:
        parentId = pic.get_parent_id(parts)
        parentPath = find_folder(parentId)
        refresh_folder(parentPath)
        if id in folders:
            return folders[id]
    return None

def refresh_folder(path):
    for ent in os.scandir(path):
        if ent.is_dir():
            parts = pic.parse_folder(ent.name)
            if parts:
                folders[parts.id] = ent.path
