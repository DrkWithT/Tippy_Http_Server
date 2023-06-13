"""
    @file consts.py
    @author Derek Tan
"""

# General:

HTTP_METHODS = {
    "HEAD": 0,
    "GET": 1
}

HTTP_SCHEMA = "HTTP/1.1"

# Statuses:

HTTP_STATS = {
    "200": "OK",
    "400": "Bad Request",
    "404": "Not Found",
    "500": "Server Error",
    "501": "Not Implemented"
}

# Message Punctuation:

HTTP_SP = " "
HTTP_HDR_SP = ":"
HTTP_ENDL = "\r\n"

