# shoebox.metadict

import os, json
from tkit import environ
from shoebox import metacache

metaFileName = "meta.json"

class MetaDict:
    def __init__(self, folderPath, env=None):
        self.folderPath = folderPath
        self.lastTouch = 0
        self.changed = False
        path = os.path.join(folderPath, metaFileName)
        try:
            with open(path, mode='r', encoding='UTF-8') as f:
                self.dict = json.load(f)
        except FileNotFoundError:
            self.dict = {}
        except json.JSONDecodeError as e:
            environ.log_error(env, "JSON error in {}: {}".format(path, str(e)))
            self.dict = {}

    def write(self, env=None, force=False):
        if self.changed or force:
            self.changed = False
            path = os.path.join(self.folderPath, metaFileName)
            try:
                with open(path, mode='w', encoding='UTF-8') as f:
                    json.dump(self.dict, f, indent=2)
            except Exception as e:
                environ.log_error(env, "Error writing {}: {}".format(path, str(e)))

    def get_meta(self, id):
        try:
            return self.dict[id]
        except KeyError:
            return {}

    def set_meta(self, id, meta):
        self.dict[id] = meta
        self.changed = True

    def apply_meta(self, id, meta):
        if id in self.dict:
            self.dict[id].update(meta)
            self.changed = True
        else:
            self.set_meta(id, meta)

    def get_default(self, prop):
        if prop == "rating":
            return 0
        else:
            return ""

    def get_value(self, id, prop, default=None):
        try:
            return self.dict[id][prop]
        except KeyError:
            if default is None:
                return self.get_default(prop)
            else:
                return default

    def set_value(self, id, prop, val):
        if id not in self.dict:
            self.dict[id] = {}
        self.dict[id][prop] = val
        self.changed = True

    def get_caption(self, id):
        return self.get_value(id, 'caption')

    def set_caption(self, id, caption):
        self.set_value(id, 'caption', caption)

    def get_rating(self, id):
        return self.get_value(id, 'rating')

    def set_rating(self, id, rating):
        self.set_value(id, 'rating', rating)

    def touch(self, value):
        self.lastTouch = value

    # remove metadata from dictionary
    # if path specified copy metadata to loose cache
    def remove_meta(self, id, path=None):
        if id in self.dict:
            if path:
                metacache.add_loose_meta(path, self.dict[id])
            del self.dict[id]
            self.changed = True

    # if named file has metadata in loose cache, add to this dictionary
    def restore_meta_from_loose_cache(self, id, name):
        path = os.path.join(self.folderPath, name)
        meta = metacache.get_loose_meta(path, remove=True)
        if meta:
            self.apply_meta(id, meta)