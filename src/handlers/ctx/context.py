"""
    @file context.py
    @author Derek Tan
"""

import time
import utils.rescache as resources

class HandlerCtx:
    """
        @description Encapsulates reusable data and functions for any application handler.
    """
    def __init__(self, rescache: resources.ResourceCache):
        self.resources = rescache
        self.attributes = {}

    def get_gmt_str(self):
        """
            @description Makes a GMT time string for all responses. This is a helper method!
        """
        # Get raw time!
        now = time.gmtime()
        secs = now.tm_sec
        secs_str = None

        # NOTE: python time structs use leap seconds up to 61s, so I must normalize them in 0 to 59s ranges!
        if secs > 59:
            secs = secs % 60

        if secs < 10:
            secs_str = f'0{secs}'
        else:
            secs_str = f'{secs}'

        return time.strftime("%a, %d %b %Y %H:%M:") + f'{secs_str} GMT'

    def get_resource(self, name):
        return self.resources.get_item(name)

    def set_attr(self, name, data):
        self.attributes[name] = data

    def get_attr(self, name):
        self.attributes.get(name)
