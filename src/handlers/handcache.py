"""
    @file handcache.py
    @author Derek Tan
"""

class HandlerCache:
    def __init__(self):
        self.path_table = {}
        self.handlers = []
        self.fallback = None

    def add_handler(self, paths: list[str], handler=None):
        if not handler or not paths:
            return False

        if len(paths) < 1:
            return False

        self.handlers.append(handler)
        new_index = len(self.handlers) - 1

        for path in paths:
            self.path_table[path] = new_index

        return True
    
    def get_handler(self, path: str):
        handler_index = self.path_table.get(path)

        if handler_index is None:
            return self.fallback

        return self.handlers[handler_index]
    
    def set_fallback_handler(self, fallback = None):
        self.fallback = fallback
