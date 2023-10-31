"""
    @file main.py\n
    @description Contains app handlers and startup code.\n
    @todo Add decorators for handler functions to modularize HEAD-GET responding code.\n
    @author Derek Tan
"""

import atexit  # For key interrupt handler
import json
from http1.request import SimpleRequest
from http1.scanner import HttpScanner
from http1.sender import SimpleSender, RES_ERR_BODY, RES_GET_BODY, RES_HEAD_BODY
from handlers.ctx.context import HandlerCtx

from core.instance import Tippy, TIPPY_VERSION_STRING

my_server = None

# MISC. HELPERS

def get_config_json(file_path: str):
    """
        @description Reads a config file for the server startup.
    """
    result = {
        "serveaddr": "localhost",
        "port": 8080
    }

    fs = None
    file_size = 0
    raw_json = None

    try:
        fs = open(file_path, "r")

        fs.seek(0, 2)
        file_size = fs.tell()
        fs.seek(0, 0)

        raw_json = fs.read(file_size)
        result = json.loads(raw_json)
    except OSError as err:
        print(err.with_traceback(err))
    except Exception as ex:
        print(ex.with_traceback(ex))
    else:
        if fs is not None:
            fs.close()

    return result

# HANDLERS

def handle_fallback(context: HandlerCtx, request: SimpleRequest, response: SimpleSender):
    last_res = request.before_close()

    response.send_heading("404")
    response.send_header("Date", context.get_gmt_str())

    if last_res:
        response.send_header("Connection", "Close")
    else:
        response.send_header("Connection", "Keep-Alive")

    response.send_header("Server", TIPPY_VERSION_STRING)

    if request.method == "HEAD":
        return response.send_body(RES_HEAD_BODY, "*/*", b'')
    else:
        return response.send_body(RES_ERR_BODY, "*/*", b'')

def handle_favicon(context: HandlerCtx, request: SimpleRequest, response: SimpleSender):
    temp_resource = context.get_resource(request.path)
    last_res = request.before_close()

    response.send_heading("200")
    response.send_header("Date", context.get_gmt_str())

    if last_res:
        response.send_header("Connection", "Close")
    else:
        response.send_header("Connection", "Keep-Alive")

    response.send_header("Server", TIPPY_VERSION_STRING)

    if request.method == "HEAD":
        return response.send_body(RES_HEAD_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())
    else:
        return response.send_body(RES_GET_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())

def handle_index(context: HandlerCtx, request: SimpleRequest, response: SimpleSender):
    temp_resource = context.get_resource(request.path)
    last_res = request.before_close()

    response.send_heading("200")
    response.send_header("Date", context.get_gmt_str())

    if last_res:
        response.send_header("Connection", "Close")
    else:
        response.send_header("Connection", "Keep-Alive")

    response.send_header("Server", TIPPY_VERSION_STRING)

    if request.method == "HEAD":
        return response.send_body(RES_HEAD_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())
    else:
        return response.send_body(RES_GET_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())

def handle_info(context: HandlerCtx, request: SimpleRequest, response: SimpleSender):
    temp_resource = context.get_resource(request.path)
    last_res = request.before_close()

    response.send_heading("200")
    response.send_header("Date", context.get_gmt_str())

    if last_res:
        response.send_header("Connection", "Close")
    else:
        response.send_header("Connection", "Keep-Alive")

    response.send_header("Server", TIPPY_VERSION_STRING)

    if request.method == "HEAD":
        return response.send_body(RES_HEAD_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())
    else:
        return response.send_body(RES_GET_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())

def handle_css(context: HandlerCtx, request: SimpleRequest, response: SimpleSender):
    temp_resource = context.get_resource(request.path)
    last_res = request.before_close()

    response.send_heading("200")
    response.send_header("Date", context.get_gmt_str())

    if last_res:
        response.send_header("Connection", "Close")
    else:
        response.send_header("Connection", "Keep-Alive")
    response.send_header("Server", TIPPY_VERSION_STRING)

    if request.method == "HEAD":
        return response.send_body(RES_HEAD_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())
    else:
        return response.send_body(RES_GET_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())

def interrupt_handler():
    """
        @summary This is an `atexit` handler. This closes and stops the listening producer before stopping all workers. No race conditions may occur since the closings in the `Tippy.stop_service` method are done in order.\n
        @author Derek Tan
    """
    my_server.stop_service()
    print('Stopped Tippy.')

# RUN SERVER

atexit.register(interrupt_handler)  # NOTE This handles SIGINTs (CTRL+C) to gracefully close the server.

config_dict = get_config_json('./config.json')
my_server = Tippy(host_name=config_dict['serveaddr'], host_port=config_dict['port'], backlog=config_dict['backlog'])

my_server.set_fallback_handler(handle_fallback)
my_server.set_handler(["/index.html"], handle_index)
my_server.set_handler(["/info.html"], handle_info)
my_server.set_handler(["/style.css"], handle_css)
my_server.set_handler(["/favicon-32x32.png", "/favicon.ico"], handle_favicon)

my_server.run_service()
