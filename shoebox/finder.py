# shoebox.finder

import os
from shoebox import pic

# folder ID to path
folders = {"": "."}

# file ID to path
cache = {}

def find_folder(id, parts=None):
    """return folder path for specified folder ID or None if not found"""
    if id in folders:
        return folders[id]
    if not parts:
        parts = pic.parse_folder(id)
    if parts:
        parentId = pic.get_parent_id(parts)
        parentPath = find_folder(parentId)
        refresh_folder(parentPath)
        if id in folders:
            return folders[id]
    return None

def find_file(id, parts=None):
    """return file path for specified picture or video ID or None if not found"""
    if id in cache:
        return cache[id];
    if not parts:
        parts = pic.parse_file(id)
    if parts:
        folderId = pic.get_folder_id(parts)
        folderPath = find_folder(folderId)
        refresh_folder(folderPath)
        if id in cache:
            return cache[id]
    return None

def refresh_folder(path):
    for ent in os.scandir(path):
        if ent.is_dir():
            parts = pic.parse_folder(ent.name)
            if parts:
                folders[parts.id] = ent.path
        else:
            parts = pic.parse_file(ent.name)
            if parts:
                cache[parts.id] = ent.path

def clear_cache():
    cache = {}
