# shoebox.contents

import os, json
from tkit import environ

contentsFileName = "contents.json"

class Contents:
    def __init__(self, folderPath, env=None, okToCreate=True):
        self.folderPath = folderPath
        path = self.get_path()
        try:
            with open(path, mode='r', encoding='UTF-8') as f:
                self.dict = json.load(f)
        except FileNotFoundError as e:
            if okToCreate:
                self.dict = {}
            else:
                raise e
        except json.JSONDecodeError as e:
            environ.log_error(env, "JSON error in {}: {}".format(path, str(e)))
            self.dict = {}
        # break out the container arrays and metadata overrides, create if necessary
        self.pictures = self.dict['pictures'] if 'pictures' in self.dict else []
        self.videos = self.dict['videos'] if 'videos' in self.dict else []
        self.folders = self.dict['folders'] if 'folders' in self.dict else []
        self.meta = self.dict['meta'] if 'meta' in self.dict else {}

    def write(self, env=None):
        # update and/or add missing container arrays and metadata overrides (but only if nonempty)
        if 'pictures' in self.dict or len(self.pictures):
            self.dict['pictures'] = self.pictures
        if 'videos' in self.dict or len(self.videos):
            self.dict['videos'] = self.videos
        if 'folders' in self.dict or len(self.folders):
            self.dict['folders'] = self.folders
        if 'meta' in self.dict or len(self.meta.keys()):
            self.dict['meta'] = self.meta
        path = self.get_path()
        try:
            with open(path, mode='w', encoding='UTF-8') as f:
                json.dump(self.dict, f, indent=2)
        except Exception as e:
            environ.log_error(env, "Error writing {}: {}".format(path, str(e)))

    def get_path(self):
        return os.path.join(self.folderPath, contentsFileName)
