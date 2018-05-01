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
        #except as e:
            # json error..
            #pass

    def get_meta(self, id):
        return self.dict[id] if id in self.dict else {}

    def get_caption(self, id):
        try:
            return self.dict[id]['caption']
        except KeyError:
            return ""

    def touch(self, value):
        self.lastTouch = value
