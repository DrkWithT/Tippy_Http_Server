"""
    @file resources.py
    @author Derek Tan
"""

import calendar
import time
import os

FS_SEEK_START = 0
FS_SEEK_END = 2
MIME_TYPE_TEXT = "text/plain"
MIME_TYPE_HTML = "text/html"
MIME_TYPE_CSS = "text/css"
MIME_TYPE_PNG = "image/png"
MIME_TYPE_ANY = "*/*"  # NOTE: assume MIME any type as raw binary!

FILE_EXTS_TO_MIME = {
    "txt": MIME_TYPE_TEXT,
    "html": MIME_TYPE_HTML,
    "css": MIME_TYPE_CSS,
    "png": MIME_TYPE_PNG,
    "foo": MIME_TYPE_ANY
}

class StaticResource:
    """
        @description Encapsulates data for a static file resource.
    """
    def __init__(self, file_path: str):
        self.type = MIME_TYPE_ANY
        self.data = None
        self.length = 0
        self.modify_date = None

        dot_pos = file_path.find(".", 1)
        file_ext = "foo"

        if dot_pos > 0:
            file_ext = file_path[dot_pos + 1 : ]
            self.type = FILE_EXTS_TO_MIME[file_ext]
        else:
            self.type = FILE_EXTS_TO_MIME["foo"]

        file_stream = open(file_path, "rb")
        file_stream.seek(0, FS_SEEK_END)
        file_length = file_stream.tell()
        file_stream.seek(0, FS_SEEK_START)

        self.data = file_stream.read(file_length)
        self.length = file_length
        self.modify_date = calendar.timegm(time.gmtime(os.stat(path=file_path).st_mtime))

        file_stream.close()

    def get_mime_type(self):
        return self.type
    
    def get_content_len(self):
        return self.length

    def get_modify_date(self):
        return self.modify_date

    def as_bytes(self):
        return self.data
    
    def as_text(self):
        return self.data.decode(encoding="ascii")
