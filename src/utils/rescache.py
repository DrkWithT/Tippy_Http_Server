"""
    @file rescache.py
    @author Derek Tan
"""

import os
import utils.resources as resources

class ResourceCache:
    """
        @description Stores a mapping of names to pre-loaded files to serve.
    """
    def __init__(self, public_dirname: str):
        self.indexes = {}  # NOTE: maps file names to resource objects.

        dir_entry = os.scandir(public_dirname)

        for item in dir_entry:
            if item.is_file():
                self.add_item(item.name, resources.StaticResource(item.path))

        dir_entry.close()
    
    def add_item(self, file_name: str, res_obj: resources.StaticResource):
        self.indexes[file_name] = res_obj

    def get_item(self, file_name: str):
        return self.indexes.get(file_name)
