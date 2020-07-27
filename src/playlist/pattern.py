import logging
import os
import random

EXTENTIONS = ('.mp3')

class Pattern():
    def __init__(self, name, root_paths=None, number=1, extentions=EXTENTIONS, cashe=None):
        self.log = logging.getLogger('MilongaPlayer.Pattern')
        self.name = name
        self.number = number
        self.extentions = extentions
        self.files = []
        self.playlist = []
        self.cashe = {} if cashe is None else cashe
        if isinstance(root_paths, list):
            self.root_paths = root_paths
        elif root_paths:
            self.root_paths = [root_paths]
        else:
            self.root_paths = []
            
        self.scan()
        self.select_files()

    def __repr__(self):
        return f'Pattern({self.root_paths}, {self.number}, {self.extentions})'

    def __len__(self):
        return len(self.playlist) 

    def next(self):
        if self.playlist:
            return self.playlist.pop(0)
        else:
            self.log.warning('Playlist is empty')
        
    def scan(self):
        for path in self.root_paths:
            self.log.debug(f'Scaning root path: {path}')
            self.scan_path(path)

    def scan_path(self, path):
        if path in self.cashe:
            self.log.debug(f'Found path "{path}" in cashe')
            self.files.extend(self.cashe[path])
            return
        self.cashe[path] = []
        for root, dirs, files in os.walk(path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if os.path.splitext(path)[1] in self.extentions:
                    if not file_path in self.files:
                        self.files.append(file_path)
                        self.cashe[path].append(file_path)

    def add_path(self, path):
        self.log.info(f'Adding path: {path}')
        if not path in self.root_paths:
            self.root_paths.append(path)
            self.scan_path(path)

    def remove_path(self, path):
        self.log.info(f'Removing path: {path}')
        self.root_paths.remove(path)
        self.files = [f for f in self.files if not f.startswith(path)]

    def select_files(self):
        if self.files:
            self.playlist = random.sample(self.files, self.number)
            self.log.debug(f'Selected the following files: {",".join(self.playlist)}')
            return self.playlist

    def insert_file(self, path, index=0):
        self.playlist.insert(index, path)
