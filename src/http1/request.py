"""
    @file request.py
    @author Derek Tan
"""

import calendar
import time
import http1.consts as consts

class SimpleRequest:
    def __init__(self, method_name="HEAD", rel_path="/"):
        self.method = method_name
        self.path = rel_path
        self.headers = {}
        self.body_data = None

    def get_header(self, header_name=""):
        result = self.headers.get(header_name)

        if result is None:
            return ""

        return result

    def put_header(self, header_name=None, header_value=None):
        if header_name is None or header_value is None:
            return False

        self.headers[header_name] = header_value

        return True

    def get_body(self):
        return self.body_data

    def put_body(self, data: bytes):
        self.body_data = data

    def method_supported(self):
        return consts.HTTP_METHODS[self.method] is not None

    def get_check_modify_date(self):
        """
            @note The GMT string returned here must be converted to a python time object before comparing!
        """
        request_mod_time = time.strptime(self.get_header("if-modified-since"), "%a, %d %b %Y %H:%M:%S GMT")

        return calendar.timegm(request_mod_time)

    def get_check_same_date(self):
        """
            @note The GMT string returned here must be converted to a python time object before comparing!
        """
        request_unmod_time = time.strptime(self.get_header("if-unmodified-since"), "%a, %d %b %Y %H:%M:%S GMT")

        return calendar.timegm(request_unmod_time)

    def before_close(self):
        return self.get_header("connection") == "Close"

    def __str__(self):
        return f'{self.method} {self.path} {consts.HTTP_SCHEMA} {self.headers}'
