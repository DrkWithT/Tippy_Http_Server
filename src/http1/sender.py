"""
    @file sender.py
    @author Derek Tan
"""

import socket
import http1.consts as consts

RES_HEAD_BODY = 0
RES_GET_BODY = 1
RES_ERR_BODY = 2

class SimpleSender:
    def __init__(self, out_stream: socket.SocketIO):
        self.writer = out_stream
    
    def send_heading(self, status_code: str):
        checked_stat_code = status_code
        temp_stat_msg = consts.HTTP_STATS[checked_stat_code]

        if temp_stat_msg is None:
            checked_stat_code = "501"
            temp_stat_msg = consts.HTTP_STATS[checked_stat_code]
        
        temp_buf = f'{consts.HTTP_SCHEMA} {checked_stat_code} {temp_stat_msg}{consts.HTTP_ENDL}'.encode(encoding="ascii")

        return self.writer.write(temp_buf) > 0

    def send_header(self, header_name: str, header_value: str):
        temp_buf = f'{header_name}: {header_value}{consts.HTTP_ENDL}'.encode(encoding="ascii")

        return self.writer.write(temp_buf) > 0

    def send_body(self, body_code: int, mime_str: str, body_data: bytes):
        write_ok = False
        
        if body_code == RES_GET_BODY:
            self.send_header("Content-Type", mime_str)
            self.send_header("Content-Length", f'{len(body_data)}')
            self.writer.write(consts.HTTP_ENDL.encode(encoding="ascii"))
            write_ok = self.writer.write(body_data) > 0
        elif body_code == RES_HEAD_BODY:  # NOTE: if omit_flag is present, write headers for peeked resource only for HEAD reqs.
            self.send_header("Content-Type", mime_str)
            self.send_header("Content-Length", f'{len(body_data)}')
            write_ok = self.writer.write(consts.HTTP_ENDL.encode(encoding="ascii"))
        else:  # NOTE: otherwise, write an empty body for a non-HEAD reply such as an HTTP or server error message.
            self.send_header("Content-Type", "*/*")
            self.send_header("Content-Length", "0")
            write_ok = self.writer.write(consts.HTTP_ENDL.encode(encoding="ascii"))

        self.writer.flush()

        return write_ok
