# shoebox.metadict

import os, json
from tkit import environ

class MetaDict:
    def __init__(self, folderPath, env=None):
        self.folderPath = folderPath
        self.lastTouch = 0
        try:
            with open(os.path.join(folderPath, "meta.json"), mode='r', encoding='UTF-8') as f:
                self.dict = json.load(f)
        except FileNotFoundError as e:
            self.dict = {}
        except json.JSONDecodeError as e:
            environ.log_error(env, "JSON error in {}: {}".format(folderPath, str(e)))
            self.dict = {}

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

    def get_rating(self, id):
        try:
            return self.dict[id]['rating']
        except KeyError:
            return 0

    def touch(self, value):
        self.lastTouch = value
