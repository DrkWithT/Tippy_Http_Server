"""
    @file scanner.py
    @author Derek Tan
"""

import socket
import http1.consts as consts
import http1.request as requests

# Notes:
"""
    HttpScanner.state:
    0,  # IDLE
    1,  # HEADING
    2,  # HEADER
    3,  # BLANK
    4,  # BODY
    5,  # END
    6   # ERROR
"""

# State Aliases:
SCANNER_ST_IDLE = 0
SCANNER_ST_HEADING = 1
SCANNER_ST_HEADER = 2
SCANNER_ST_BODY = 3
SCANNER_ST_END = 4
SCANNER_ST_ERROR = 5

class HttpScanner:
    def __init__(self, in_stream: socket.SocketIO):
        # Reader state:
        self.state = SCANNER_ST_IDLE

        # File stream from socket:
        self.reader = in_stream
        
        # List of status line tokens:
        self.temps = None

        # Header lookup and cache dict:
        self.hdr_cache = {
            "host": None,
            "connection": None,
            "content-type": None,
            "content-length": None,
        }

        # Cache for bytes to put in request object:
        self.temp_data = None

    def reset(self):
        self.state = SCANNER_ST_IDLE
        self.temps = None
        self.hdr_cache["host"] = None
        self.hdr_cache["connection"] = None
        self.hdr_cache["content-type"] = None
        self.hdr_cache["content-length"] = None
        self.temp_data = None

    def state_heading(self, line: str):
        print(f'heading line blank? {len(line) < 1}')  # DEBUG!
        tokens = line.split(consts.HTTP_SP)

        if len(tokens) != 3:
            return SCANNER_ST_ERROR

        self.temps = tokens[0 : 3]

        return SCANNER_ST_HEADER

    def state_header(self, line: str):
        print(f'header line? {line}')  # DEBUG!
        if not line:
            return SCANNER_ST_BODY

        first_colon_pos = -1

        try:
            first_colon_pos = line.index(consts.HTTP_HDR_SP) 
        except:
            return SCANNER_ST_ERROR
        
        header_name = line[0 : first_colon_pos].strip().lower()
        header_value = line[first_colon_pos + 1 :].strip()

        if self.hdr_cache.get(header_name) is None:
            self.hdr_cache[header_name] = header_value
        
        return SCANNER_ST_HEADER

    def state_body(self, content_len = 0):
        self.temp_data = self.reader.read(content_len)
        
        return SCANNER_ST_END

    def next_request(self):
        temp_line = None

        while self.state != SCANNER_ST_END:
            print(f'HttpScanner.state = {self.state}')  # DEBUG!

            if self.state == SCANNER_ST_IDLE:
                # Begin state!
                self.state = SCANNER_ST_HEADING
            elif self.state == SCANNER_ST_HEADING:
                # Process status line...
                self.reader.flush()
                temp_line = self.reader.readline().strip()
                self.state = self.state_heading(temp_line)
            elif self.state == SCANNER_ST_HEADER:
                # Process header...
                temp_line = self.reader.readline().strip()
                self.state = self.state_header(temp_line)
            elif self.state == SCANNER_ST_BODY:
                # Process body:
                clen_str = self.hdr_cache["content-length"]
                cont_len = 0

                # NOTE: parse content-length only if available!
                if clen_str is not None:
                    cont_len = int(clen_str)
                
                self.state = self.state_body(cont_len)
            elif self.state == SCANNER_ST_END:
                pass
            else:
                raise Exception("Invalid HTTP msg syntax!")
        
        # TODO: Check req_schema for "HTTP/1.1"?
        req_method, req_path, req_schema = self.temps

        request = requests.SimpleRequest(req_method, req_path)

        # NOTE: load headers!
        for hkey in self.hdr_cache:
            request.put_header(hkey, self.hdr_cache[hkey])

        request.put_body(self.temp_data);

        return request
