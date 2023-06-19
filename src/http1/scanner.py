"""
    @file scanner.py
    @author Derek Tan
"""

import socket
import http1.consts as consts
import http1.request as requests

# State Aliases:
SCANNER_ST_IDLE = 0
SCANNER_ST_HEADING = 1
SCANNER_ST_HEADER = 2
SCANNER_ST_BODY = 3
SCANNER_ST_CHUNK_LEN = 4
SCANNER_ST_CHUNK_BLOB = 5
SCANNER_ST_END = 6
SCANNER_ST_ERROR = 7

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
            "transfer-encoding": None,
            "if-modified-since": None,
            "if-unmodified-since": None,
            "cache-control": None
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
        self.hdr_cache["transfer-encoding"] = None
        self.hdr_cache["if-modified-since"] = None
        self.hdr_cache["if-unmodified-since"] = None
        self.hdr_cache["cache-control"] = None
        self.temp_data = None

    def state_heading(self, line: str):
        tokens = line.split(consts.HTTP_SP)

        if len(tokens) != 3:
            return SCANNER_ST_ERROR

        self.temps = tokens[0 : 3]

        return SCANNER_ST_HEADER

    def state_header(self, line: str):
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
        if self.hdr_cache["transfer-encoding"] == "chunked":
            return SCANNER_ST_CHUNK_LEN

        self.temp_data = self.reader.read(content_len)

        return SCANNER_ST_END

    def state_chunk_len(self, line: str):
        if line is None:
            return SCANNER_ST_END

        if len(line) > 0:  # NOTE chunk length lines are usually ignored, so just check for their presence.
            return SCANNER_ST_CHUNK_BLOB

        return SCANNER_ST_END

    def state_chunk_blob(self, chunk_line: str):
        if len(chunk_line) > 0:
            temp_chunk_data = chunk_line.encode(encoding="ascii")
            temp_chunk_size = len(temp_chunk_data)

            self.temp_data.join(temp_chunk_data)
            self.hdr_cache["content-length"] += temp_chunk_size

            return SCANNER_ST_CHUNK_LEN

        return SCANNER_ST_END

    def next_request(self):
        temp_line = None

        while self.state != SCANNER_ST_END:
            # print(f'HttpScanner.state = {self.state}')  # DEBUG!

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
                else:
                    self.hdr_cache["content-length"] = 0
                    cont_len = 0

                self.state = self.state_body(cont_len)
            elif self.state == SCANNER_ST_CHUNK_LEN:
                temp_line = self.reader.readline().strip()
                self.state = self.state_chunk_len(temp_line)
            elif self.state == SCANNER_ST_CHUNK_BLOB:
                temp_line = self.reader.readline().strip()
                self.state = self.state_chunk_blob(temp_line)
            elif self.state == SCANNER_ST_END:
                pass
            else:
                raise Exception("Invalid HTTP msg syntax!")

        # TODO: Put req_schema into request object for checking http version support. Versions affect how request processing works: Host is not needed for 1.0, for example.
        req_method, req_path, req_schema = self.temps

        request = requests.SimpleRequest(req_method, req_path)

        # NOTE: load headers!
        for hkey in self.hdr_cache:
            request.put_header(hkey, self.hdr_cache[hkey])

        request.put_body(self.temp_data);

        return request
