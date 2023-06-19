"""
    @file rescache.py
    @author Derek Tan
    @todo Fix resource cache to accept relative paths besides file names.
"""

import os
import utils.resources as resources

class ResourceCache:
    """
        @description Stores a mapping of names to pre-loaded files to serve.
    """
    def __init__(self, public_dirname: str):
        self.indexes = {}  # NOTE: maps paths to resource indexes
        self.resources = []  # NOTE: maps indexes to resources

        dir_entry = os.scandir(public_dirname)

        for item in dir_entry:
            if item.is_file():
                self.add_item(item.name, resources.StaticResource(item.path))

        dir_entry.close()
    
    def add_item(self, file_name: str, res_obj: resources.StaticResource):
        """
            @description Adds a static resource to this cache.
            @note The very first path to this resource will be formatted as `"/<file name>"`!
        """
        self.resources.append(res_obj)
        top_index = len(self.resources) - 1
        self.indexes[f'/{file_name}'] = top_index

    def add_item_paths(self, res_paths: list[str]):
        """
            @description Adds alternate request paths for a given resource.
            @note The first item in res_paths must follow the format `/<file name>` to target a resource by that original alias.
        """
        if len(res_paths) < 1:
            return False

        pre_index = self.indexes.get(res_paths[0])

        if pre_index is None:
            return False

        alias_paths = res_paths[1:]

        for path in alias_paths:
            self.indexes[path] = pre_index

        return True

    def get_item(self, res_path: str):
        res_index = self.indexes.get(res_path)

        if res_index is None:
            return None

        return self.resources[res_index]
