# shoebox.metadict

import os, json
from tkit import environ

metaFileName = "meta.json"

class MetaDict:
    def __init__(self, folderPath, env=None):
        self.folderPath = folderPath
        self.lastTouch = 0
        path = os.path.join(folderPath, metaFileName)
        try:
            with open(path, mode='r', encoding='UTF-8') as f:
                self.dict = json.load(f)
        except FileNotFoundError:
            self.dict = {}
        except json.JSONDecodeError as e:
            environ.log_error(env, "JSON error in {}: {}".format(path, str(e)))
            self.dict = {}

    def write(self, env=None):
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

    def get_caption(self, id):
        try:
            return self.dict[id]['caption']
        except KeyError:
            return ""

    def set_caption(self, id, caption):
        if id not in self.dict:
            self.dict[id] = {}
        self.dict[id]['caption'] = caption

    def get_rating(self, id):
        try:
            return self.dict[id]['rating']
        except KeyError:
            return 0

    def set_rating(self, id, rating):
        if id not in self.dict:
            self.dict[id] = {}
        self.dict[id]['rating'] = rating

    def touch(self, value):
        self.lastTouch = value
